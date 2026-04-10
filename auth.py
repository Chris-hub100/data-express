"""
auth.py — Westruck Operations Suite · Layer 1 Security
JWT-based authentication endpoints.

Dependencies (add to requirements.txt):
    PyJWT>=2.8.0
    bcrypt>=4.1.0

Environment variables required:
    JWT_SECRET          — long random string, min 32 chars
    ADMIN_ID            — owner master ID (existing)
    ADMIN_PIN           — owner master PIN (existing)
    JWT_EXPIRY_HOURS    — defaults to 8 (one working shift)
"""

import os
import time
import jwt
import bcrypt
import hashlib
from functools import wraps
from flask import Blueprint, request, jsonify, g
from firebase_admin import firestore
from werkzeug.security import generate_password_hash, check_password_hash

# ── Blueprint ──────────────────────────────────────────────────────
auth_bp = Blueprint('auth', __name__)

# ── Configuration ─────────────────────────────────────────────────
JWT_SECRET       = os.environ.get('JWT_SECRET', 'CHANGE_THIS_IN_PRODUCTION_MIN_32_CHARS!!')
JWT_ALGORITHM    = 'HS256'
JWT_EXPIRY_HOURS = int(os.environ.get('JWT_EXPIRY_HOURS', 8))

# Rate limiting — simple in-memory store (swap for Redis in production)
_login_attempts: dict = {}   # { ip: { count: int, window_start: float } }
MAX_ATTEMPTS    = 5
ATTEMPT_WINDOW  = 300        # 5 minutes in seconds


# ── Helpers ────────────────────────────────────────────────────────

def _get_db():
    """Lazy Firestore client — avoids import-time errors if firebase not init."""
    return firestore.client()


def _rate_limit_check(ip: str) -> bool:
    """Returns True if request is allowed, False if rate limited."""
    now = time.time()
    entry = _login_attempts.get(ip, {'count': 0, 'window_start': now})

    # Reset window if expired
    if now - entry['window_start'] > ATTEMPT_WINDOW:
        entry = {'count': 0, 'window_start': now}

    entry['count'] += 1
    _login_attempts[ip] = entry

    return entry['count'] <= MAX_ATTEMPTS


def _mint_token(dispatcher_id: str, node_id: str, role: str,
                display_name: str, jti: str) -> tuple[str, int]:
    """
    Mints a signed JWT.
    Returns (token_string, exp_timestamp).
    """
    exp = int(time.time()) + (JWT_EXPIRY_HOURS * 3600)
    payload = {
        'sub': dispatcher_id,       # subject — dispatcher ID
        'node': node_id,            # which firm node
        'role': role,               # 'owner' | 'dispatcher'
        'name': display_name,
        'jti': jti,                 # unique token ID — used for session invalidation
        'iat': int(time.time()),    # issued at
        'exp': exp,                 # expiry
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, exp


def _verify_token(token: str) -> dict | None:
    """
    Decodes and verifies a JWT.
    Returns payload dict or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _get_bearer_token() -> str | None:
    """Extracts Bearer token from Authorization header."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None


def _hash_jti(jti: str) -> str:
    """Stores a hash of the JTI in Firestore, not the raw token."""
    return hashlib.sha256(jti.encode()).hexdigest()


# ── Decorators ────────────────────────────────────────────────────

def require_auth(f):
    """
    Route decorator — validates JWT on every protected endpoint.
    Injects g.dispatcher_id, g.node_id, g.role into Flask globals.

    Usage:
        @app.route('/api/some-route', methods=['POST'])
        @require_auth
        def some_route():
            role = g.role  # 'owner' or 'dispatcher'
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _get_bearer_token()
        if not token:
            return jsonify({'success': False, 'message': 'No token provided'}), 401

        payload = _verify_token(token)
        if not payload:
            return jsonify({'success': False, 'message': 'Session expired'}), 401

        # Check JTI against Firestore (single-session enforcement)
        try:
            db = _get_db()
            node_id = payload.get('node')
            dispatcher_id = payload.get('sub')
            stored_jti_hash = _hash_jti(payload.get('jti', ''))

            account_ref = (
                db.collection('artifacts').document(node_id)
                  .collection('private').document('dispatchers')
                  .collection('accounts').document(dispatcher_id)
            )
            account_doc = account_ref.get()

            if not account_doc.exists:
                return jsonify({'success': False, 'message': 'Account not found'}), 401

            account_data = account_doc.to_dict()

            # Block suspended accounts mid-session
            if not account_data.get('is_active', False):
                return jsonify({'success': False, 'message': 'Account suspended'}), 403

            # Validate JTI — rejects old tokens after new login
            if account_data.get('active_jti_hash') != stored_jti_hash:
                return jsonify({'success': False, 'message': 'Session invalidated'}), 401

        except Exception as e:
            print(f'[Auth Middleware Error] {e}')
            return jsonify({'success': False, 'message': 'Auth verification failed'}), 500

        # Inject into Flask request globals
        g.dispatcher_id = dispatcher_id
        g.node_id       = node_id
        g.role          = payload.get('role', 'dispatcher')
        g.display_name  = payload.get('name', dispatcher_id)

        return f(*args, **kwargs)
    return decorated


def require_role(role: str):
    """
    Role-check decorator — must be used AFTER @require_auth.

    Usage:
        @app.route('/api/analytics/export', methods=['GET'])
        @require_auth
        @require_role('owner')
        def export_analytics():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.role != role:
                return jsonify({
                    'success': False,
                    'message': 'Insufficient permissions'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Routes ────────────────────────────────────────────────────────

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Body: { nodeId, dispatcherId, pin }
    Returns: { success, token, role, displayName, exp }

    Two credential paths:
    1. Owner login  — checks against ADMIN_ID / ADMIN_PIN env vars
    2. Dispatcher login — checks against Firestore account store
    """
    # Rate limiting
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if not _rate_limit_check(client_ip):
        return jsonify({
            'success': False,
            'message': 'Too many login attempts — try again in 5 minutes'
        }), 429

    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Request body required'}), 400

    node_id       = str(data.get('nodeId', '')).strip().lower()
    dispatcher_id = str(data.get('dispatcherId', '')).strip()
    pin           = str(data.get('pin', ''))

    if not node_id or not dispatcher_id or not pin:
        return jsonify({'success': False, 'message': 'All fields required'}), 400

    # ── PATH 1: Owner login (env vars) ────────────────────────────
    admin_id  = os.environ.get('ADMIN_ID', '')
    admin_pin = os.environ.get('ADMIN_PIN', '')

    if dispatcher_id == admin_id and pin == admin_pin:
        import secrets
        jti = secrets.token_hex(16)
        token, exp = _mint_token(
            dispatcher_id=dispatcher_id,
            node_id=node_id,
            role='owner',
            display_name='System Owner',
            jti=jti
        )
        # Store JTI hash in Firestore for session tracking
        try:
            db = _get_db()
            owner_ref = (
                db.collection('artifacts').document(node_id)
                  .collection('private').document('dispatchers')
                  .collection('accounts').document(dispatcher_id)
            )
            owner_ref.set({
                'dispatcher_id': dispatcher_id,
                'display_name': 'System Owner',
                'role': 'owner',
                'is_active': True,
                'active_jti_hash': _hash_jti(jti),
                'last_login': firestore.SERVER_TIMESTAMP,
            }, merge=True)
        except Exception as e:
            print(f'[Owner JTI Store Error] {e}')

        return jsonify({
            'success':     True,
            'token':       token,
            'role':        'owner',
            'displayName': 'System Owner',
            'exp':         exp
        }), 200

    # ── PATH 2: Dispatcher login (Firestore) ──────────────────────
    try:
        db = _get_db()
        account_ref = (
            db.collection('artifacts').document(node_id)
              .collection('private').document('dispatchers')
              .collection('accounts').document(dispatcher_id)
        )
        account_doc = account_ref.get()

        if not account_doc.exists:
            # Generic message — don't reveal whether ID exists
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401

        account = account_doc.to_dict()

        # Check suspended
        if not account.get('is_active', False):
            return jsonify({
                'success': False,
                'message': 'Account suspended'
            }), 403

        # Verify bcrypt password
        stored_hash = account.get('password_hash', '').encode('utf-8')
        if not stored_hash or not bcrypt.checkpw(pin.encode('utf-8'), stored_hash):
            return jsonify({
                'success': False,
                'message': 'Invalid credentials'
            }), 401

        # ── VALID — mint token & update JTI (invalidates prior session) ──
        import secrets
        jti = secrets.token_hex(16)
        role         = account.get('role', 'dispatcher')
        display_name = account.get('display_name', dispatcher_id)

        token, exp = _mint_token(
            dispatcher_id=dispatcher_id,
            node_id=node_id,
            role=role,
            display_name=display_name,
            jti=jti
        )

        # Overwrite active_jti_hash — invalidates any prior active session
        account_ref.update({
            'active_jti_hash': _hash_jti(jti),
            'last_login': firestore.SERVER_TIMESTAMP,
        })

        return jsonify({
            'success':     True,
            'token':       token,
            'role':        role,
            'displayName': display_name,
            'exp':         exp
        }), 200

    except Exception as e:
        print(f'[Login Error] {e}')
        return jsonify({'success': False, 'message': 'Auth service error'}), 

@auth_bp.route('/api/auth/send-broadcast', methods=['POST'])
@require_auth
@require_role('owner')
def send_broadcast():
    data = request.json
    node = data.get('targetNodeId')
    
    db = _get_db()
    msg_ref = db.collection('artifacts').document(node).collection('public').document('announcements').collection('messages').document()
    
    msg_ref.set({
        'header': data.get('header'),
        'body': data.get('body'),
        'timestamp': firestore.SERVER_TIMESTAMP,
        'author': g.dispatcher_id
    })
    return jsonify({'success': True}), 201

@auth_bp.route('/api/auth/delete-broadcast', methods=['POST'])
@require_auth
@require_role('owner')
def delete_broadcast():
    data = request.json
    node = data.get('targetNodeId')
    msg_id = data.get('messageId')
    
    db = _get_db()
    db.collection('artifacts').document(node).collection('public').document('announcements').collection('messages').document(msg_id).delete()
    
    return jsonify({'success': True}), 200


@auth_bp.route('/api/auth/verify', methods=['GET'])
def verify_session():
    """
    GET /api/auth/verify
    Header: Authorization: Bearer <token>
    Used by the dashboard on load to confirm session is still valid.
    Returns: { valid, role, displayName, nodeId, expiresIn }
    """
    token = _get_bearer_token()
    if not token:
        return jsonify({'valid': False}), 401

    payload = _verify_token(token)
    if not payload:
        return jsonify({'valid': False, 'reason': 'expired'}), 401

    expires_in = payload['exp'] - int(time.time())

    return jsonify({
        'valid':       True,
        'role':        payload.get('role'),
        'displayName': payload.get('name'),
        'nodeId':      payload.get('node'),
        'expiresIn':   expires_in          # seconds remaining
    }), 200


@auth_bp.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """
    POST /api/auth/logout
    Header: Authorization: Bearer <token>
    Invalidates the JTI in Firestore — token is dead immediately.
    """
    try:
        db = _get_db()
        account_ref = (
            db.collection('artifacts').document(g.node_id)
              .collection('private').document('dispatchers')
              .collection('accounts').document(g.dispatcher_id)
        )
        # Clear the active JTI — any subsequent request with the old token fails
        account_ref.update({
            'active_jti_hash': None,
            'last_logout': firestore.SERVER_TIMESTAMP,
        })
        return jsonify({'success': True}), 200

    except Exception as e:
        print(f'[Logout Error] {e}')
        return jsonify({'success': False}), 500


@auth_bp.route('/api/auth/create-dispatcher', methods=['POST'])
@require_auth
@require_role('owner')
def create_dispatcher():
    """
    POST /api/auth/create-dispatcher
    Owner-only. Creates a dispatcher account for a given node.
    Body: { targetNodeId, dispatcherId, displayName, pin, role? }
    """
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Body required'}), 400

    target_node   = str(data.get('targetNodeId', '')).strip().lower()
    new_disp_id   = str(data.get('dispatcherId', '')).strip()
    display_name  = str(data.get('displayName', '')).strip()
    pin           = str(data.get('pin', ''))
    role          = data.get('role', 'dispatcher')

    if not all([target_node, new_disp_id, display_name, pin]):
        return jsonify({'success': False, 'message': 'All fields required'}), 400

    if role not in ('owner', 'dispatcher'):
        return jsonify({'success': False, 'message': 'Invalid role'}), 400

    if len(pin) < 4:
        return jsonify({'success': False, 'message': 'PIN must be at least 4 characters'}), 400

    try:
        db = _get_db()

        # Check if dispatcher ID already exists for this node
        account_ref = (
            db.collection('artifacts').document(target_node)
              .collection('private').document('dispatchers')
              .collection('accounts').document(new_disp_id)
        )
        if account_ref.get().exists:
            return jsonify({'success': False, 'message': 'Dispatcher ID already exists'}), 409

        # Hash the PIN with bcrypt
        pw_hash = bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt(rounds=12))

        account_ref.set({
            'dispatcher_id': new_disp_id,
            'display_name':  display_name,
            'role':          role,
            'password_hash': pw_hash.decode('utf-8'),
            'is_active':     True,
            'active_jti_hash': None,
            'created_at':    firestore.SERVER_TIMESTAMP,
            'created_by':    g.dispatcher_id,
        })

        return jsonify({'success': True, 'dispatcherId': new_disp_id}), 201

    except Exception as e:
        print(f'[Create Dispatcher Error] {e}')
        return jsonify({'success': False, 'message': 'Failed to create account'}), 500


@auth_bp.route('/api/auth/toggle-dispatcher', methods=['POST'])
@require_auth
@require_role('owner')
def toggle_dispatcher():
    """
    POST /api/auth/toggle-dispatcher
    Owner-only. Suspends or reactivates a dispatcher account.
    Body: { targetNodeId, dispatcherId, isActive }
    """
    data = request.json
    target_node   = str(data.get('targetNodeId', '')).strip().lower()
    disp_id       = str(data.get('dispatcherId', '')).strip()
    is_active     = bool(data.get('isActive', False))

    if not target_node or not disp_id:
        return jsonify({'success': False, 'message': 'targetNodeId and dispatcherId required'}), 400

    try:
        db = _get_db()
        account_ref = (
            db.collection('artifacts').document(target_node)
              .collection('private').document('dispatchers')
              .collection('accounts').document(disp_id)
        )

        update_data = {'is_active': is_active}
        # If suspending, also invalidate their active session immediately
        if not is_active:
            update_data['active_jti_hash'] = None

        account_ref.update(update_data)

        return jsonify({'success': True}), 200

    except Exception as e:
        print(f'[Toggle Dispatcher Error] {e}')
        return jsonify({'success': False, 'message': 'Update failed'}), 500
    
@auth_bp.route('/api/auth/list-dispatchers', methods=['GET'])
@require_auth
@require_role('owner')
def list_dispatchers():
    """
    GET /api/auth/list-dispatchers
    Owner-only. Lists all accounts for the current node.
    """
    try:
        db = _get_db()
        # Path aligned with your existing 'require_auth' logic
        accounts_ref = (
            db.collection('artifacts').document(g.node_id)
              .collection('private').document('dispatchers')
              .collection('accounts')
        )
        
        docs = accounts_ref.stream()
        user_list = []
        for doc in docs:
            data = doc.to_dict()
            # Security: Strip the password hash before sending to UI
            data.pop('password_hash', None)
            user_list.append(data)
            
        return jsonify(user_list), 200

    except Exception as e:
        print(f'[List Dispatchers Error] {e}')
        return jsonify({'success': False, 'message': 'Failed to fetch team'}), 500
    

# --- 1. THE ONBOARDING HANDSHAKE (FIXED) ---
@auth_bp.route('/api/driver/onboard', methods=['POST'])
def onboard_driver():
    db = _get_db()
    data = request.json
    node_id = data.get('nodeId')
    ref_pin = data.get('referencePin')
    full_name = data.get('fullName')
    phone = data.get('phone')
    secret_pin = data.get('secretPin')
    device_id = data.get('deviceId')

    if not all([node_id, ref_pin, full_name, phone, secret_pin, device_id]):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        # A. Verify Firm & Reference PIN
        firm_ref = db.collection('artifacts').document(node_id).get()
        if not firm_ref.exists:
            return jsonify({"message": "Invalid Firm ID"}), 404
        
        firm_data = firm_ref.to_dict()
        if str(firm_data.get('onboardingPin')) != str(ref_pin):
            return jsonify({"message": "Incorrect Reference PIN"}), 401

        # B. Locate Driver Record
        driver_query = db.collection('artifacts').document(node_id)\
                         .collection('public').document('data')\
                         .collection('drivers').where('phone', '==', phone).limit(1).get()

        hashed_pin = generate_password_hash(secret_pin)

        if len(driver_query) > 0:
            # ✅ FIXED: Get the first document from the list
            driver_doc = driver_query[0]
            driver_data = driver_doc.to_dict()
            
            if driver_data.get('hasAccount'):
                return jsonify({"message": "Account already bound to a device. Contact Dispatcher."}), 403
            
            # ✅ FIXED: Use the document reference to update
            driver_doc.reference.update({
                'name': full_name,
                'hashedPin': hashed_pin,
                'deviceId': device_id,
                'hasAccount': True,
                'onboardedAt': firestore.SERVER_TIMESTAMP
            })
        else:
            # NEW ENTRY: Create a brand new driver record
            db.collection('artifacts').document(node_id)\
              .collection('public').document('data')\
              .collection('drivers').add({
                'name': full_name,
                'phone': phone,
                'hashedPin': hashed_pin,
                'deviceId': device_id,
                'hasAccount': True,
                'onboardedAt': firestore.SERVER_TIMESTAMP,
                'license': "" 
            })

        return jsonify({"message": "Onboarding Successful"}), 200

    except Exception as e:
        print(f"Onboarding Error: {e}")
        return jsonify({"message": "Internal Server Error"}), 500


# --- 2. THE DAILY VERIFICATION (FIXED) ---
@auth_bp.route('/api/driver/verify', methods=['POST'])
def verify_driver():
    db = _get_db()
    data = request.json
    node_id = data.get('nodeId')
    phone = data.get('phone')
    provided_pin = data.get('pin')
    current_device = data.get('deviceId')

    if not all([node_id, phone, provided_pin, current_device]):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        # Search for the driver by phone
        driver_query = db.collection('artifacts').document(node_id)\
                         .collection('public').document('data')\
                         .collection('drivers').where('phone', '==', phone).limit(1).get()

        if len(driver_query) == 0:
            return jsonify({"message": "Driver profile not found"}), 404

        # ✅ FIXED: Get the first document from the list
        driver_doc = driver_query[0]
        driver_data = driver_doc.to_dict()

        # A. Check Device Binding
        stored_device = driver_data.get('deviceId')
        if stored_device and stored_device != current_device:
            return jsonify({
                "message": "Device mismatch. This account is locked to another phone."
            }), 403

        # B. Check if account is active
        if not driver_data.get('hasAccount', False):
            return jsonify({
                "message": "Account not fully onboarded. Please complete registration."
            }), 403

        # C. Verify 6-Digit Secret PIN
        stored_hash = driver_data.get('hashedPin')
        if not stored_hash:
            return jsonify({"message": "Account not fully onboarded"}), 400

        # Special case: Biometric bypass (if implemented)
        if provided_pin == 'BIOMETRIC_BYPASS':
            return jsonify({
                "message": "Auth Successful",
                "driverName": driver_data.get('name', 'Driver'),
                "phone": phone
            }), 200

        # Verify the PIN
        if not check_password_hash(stored_hash, str(provided_pin)):
            return jsonify({"message": "Invalid Secret PIN"}), 401

        # Update last login timestamp
        driver_doc.reference.update({
            'lastLogin': firestore.SERVER_TIMESTAMP
        })

        return jsonify({
            "message": "Auth Successful",
            "driverName": driver_data.get('name', 'Driver'),
            "phone": phone
        }), 200

    except Exception as e:
        print(f"Verification Error: {e}")
        return jsonify({"message": "Internal Server Error"}), 500