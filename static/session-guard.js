/**
 * session-guard.js
 * Westruck Operations Suite — Layer 1 & 4 Frontend Security
 *
 * Drop this <script> block just before </body> in operations.html,
 * replacing the existing localStorage credential prompt system entirely.
 *
 * What this does:
 *  1. On load — verifies session via /api/auth/verify before showing dashboard
 *  2. Injects the JWT into every backend API call (SMS, driver endpoints)
 *  3. Watches token expiry — auto-logs out and redirects 5 minutes before expiry
 *  4. Replaces the localStorage prompt in unlockSystem() with sessionStorage reads
 *  5. Adds a session timer indicator to the nav bar
 *  6. Handles logout properly (server-side JTI invalidation + sessionStorage clear)
 *
 * INTEGRATION STEPS for operations.html:
 *  1. Remove the prompt() calls inside unlockSystem()
 *  2. Remove: localStorage.setItem('lh_aid', ...) and localStorage.setItem('lh_apin', ...)
 *  3. Replace the sendInternalSMS headers with getAuthHeaders()
 *  4. Paste this entire block just before </body>
 */


// ============================================================
// SESSION STORE — reads from sessionStorage (set by login.html)
// ============================================================
const Session = {
    getToken()       { return sessionStorage.getItem('lh_token'); },
    getRole()        { return sessionStorage.getItem('lh_role'); },
    getNode()        { return sessionStorage.getItem('lh_node'); },
    getDisplayName() { return sessionStorage.getItem('lh_dispatcher'); },
    getExp()         { return Number(sessionStorage.getItem('lh_exp')); },
    isValid()        {
        const token = this.getToken();
        const exp   = this.getExp();
        return !!token && Date.now() / 1000 < exp;
    },
    clear() {
        sessionStorage.removeItem('lh_token');
        sessionStorage.removeItem('lh_role');
        sessionStorage.removeItem('lh_node');
        sessionStorage.removeItem('lh_dispatcher');
        sessionStorage.removeItem('lh_exp');
    }
};


// ============================================================
// AUTH HEADERS — replaces localStorage-based X-Admin headers
// Call this wherever you build fetch() requests to the backend
// ============================================================
function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${Session.getToken() || ''}`
    };
}


// ============================================================
// REDIRECT TO LOGIN
// ============================================================
// --- UPDATE 1: Smarter Redirect Logic ---
function redirectToLogin(reason = 'none') {
    Session.clear();
    const params = new URLSearchParams(window.location.search);
    const node = params.get('node') || Session.getNode() || '';
    
    let targetUrl = `/login?node=${node}`;
    
    // Only append the reason if it's actually 'expired'
    if (reason === 'expired') {
        targetUrl += `&reason=expired`;
    }
    
    window.location.href = targetUrl;
}


// ============================================================
// SESSION GUARD — runs on page load, before dashboard renders
// Replaces the prompt() block inside unlockSystem()
// ============================================================
// --- UPDATE 2: Differentiating Fresh vs Expired in Load ---
async function verifySessionOnLoad() {
    const token = Session.getToken();

    // 1. FRESH VISITOR CHECK: If no token at all, send to login SILENTLY
    if (!token) {
        redirectToLogin('none'); 
        return false;
    }

    // 2. EXPIRY CHECK: If token exists but is mathematically expired
    if (!Session.isValid()) {
        redirectToLogin('expired');
        return false;
    }

    // 3. SERVER VERIFICATION: Confirm with backend
    try {
        const response = await fetch('/api/auth/verify', {
            headers: getAuthHeaders()
        });

        if (response.status === 401) {
            redirectToLogin('expired');
            return false;
        }

        const data = await response.json();
        if (!data.valid) {
            redirectToLogin('expired');
            return false;
        }

        if (data.displayName) {
            sessionStorage.setItem('lh_dispatcher', data.displayName);
        }

        return true;

    } catch (err) {
        console.warn('[Session Guard] Verification failed, using local fallback');
        return Session.isValid();
    }
}


// ============================================================
// EXPIRY WATCHER — auto-logout 5 minutes before token expires
// ============================================================
let _expiryTimer = null;

function startExpiryWatcher() {
    if (_expiryTimer) clearTimeout(_expiryTimer);

    const exp = Session.getExp();
    if (!exp) return;

    const now        = Date.now() / 1000;
    const remaining  = exp - now;
    const warnAt     = remaining - 300; // 5 minutes before expiry

    if (warnAt > 0) {
        // Show warning at 5-minute mark
        _expiryTimer = setTimeout(() => {
            showSessionExpiryWarning(300);
            // Then auto-logout at actual expiry
            setTimeout(() => {
                redirectToLogin('expired');
            }, 300 * 1000);
        }, warnAt * 1000);
    } else if (remaining > 0) {
        // Already in the warning window — logout at expiry
        setTimeout(() => redirectToLogin('expired'), remaining * 1000);
    } else {
        // Already expired
        redirectToLogin('expired');
    }
}


function showSessionExpiryWarning(secondsLeft) {
    // Inject a warning toast into the existing toast system
    const minutes = Math.ceil(secondsLeft / 60);
    const t       = document.getElementById('toast');
    const tc      = document.getElementById('toastContent');
    const ti      = document.getElementById('toastIcon');
    const tm      = document.getElementById('toastMsg');

    if (!t) return;

    tm.innerText = `Session expires in ${minutes} minute${minutes !== 1 ? 's' : ''} — save your work`;
    tc.className = 'bg-amber-600 text-white px-6 py-3 rounded-full font-bold text-sm shadow-2xl flex items-center gap-3 animate-fade';
    ti.className = 'bi bi-clock-history text-white';
    t.classList.remove('hidden');

    // Keep this toast visible longer
    setTimeout(() => t.classList.add('hidden'), 8000);
}


// ============================================================
// SESSION INDICATOR — injects dispatcher name + timer into nav
// ============================================================
function injectSessionIndicator() {
    const nav = document.querySelector('nav .container');
    if (!nav) return;

    const name = Session.getDisplayName() || 'Dispatcher';
    const role = Session.getRole() || 'dispatcher';

    const indicator = document.createElement('div');
    indicator.id = 'sessionIndicator';
    indicator.className = 'hidden md:flex flex-col items-end';
    indicator.innerHTML = `
        <div class="flex items-center gap-2">
            <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest">${role === 'owner' ? '⬡ Owner' : 'Dispatcher'}</span>
            <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
        </div>
        <p class="text-xs font-black text-slate-700 uppercase tracking-tighter">${name}</p>
    `;

    // Replace the existing "Gateway Status" div in the nav
    const existing = nav.querySelector('.hidden.md\\:flex');
    if (existing) {
        existing.replaceWith(indicator);
    } else {
        nav.appendChild(indicator);
    }
}


// ============================================================
// ROLE-BASED UI GATING
// Hides elements the current role shouldn't see.
// Add data-role="owner" to any element that should be owner-only.
// ============================================================
function applyRoleGating() {
    const role = Session.getRole(); // 'owner' or 'dispatcher'
    
    // 1. Remove any old role classes
    document.body.classList.remove('role-owner', 'role-dispatcher');
    
    // 2. Add the current role class to the body
    if (role) {
        document.body.classList.add(`role-${role}`);
        console.log(`[Security] UI Stamped for Role: ${role}`);
    }

    // 3. Keep your existing logic as a fallback for hard-removal
    document.querySelectorAll('[data-role="owner"]').forEach(el => {
        if (role !== 'owner') el.remove(); 
    });
}


// ============================================================
// PATCHED sendInternalSMS
// Replaces the old localStorage-header version in operations.html.
// Swap the function body — signature stays identical.
// ============================================================
async function sendInternalSMS(phone, status, waybill, name, isBulk = false) {
    let message = '';
    const s = status.toLowerCase();
    if (s.includes('transit'))
        message = `Hello ${name}, your package (${waybill}) is officially in transit! Track live: ledgehold.xyz/tracking`;
    else if (s.includes('arrived'))
        message = `Hello ${name}, your package (${waybill}) has arrived at the destination!`;
    else
        message = `Hello ${name}, waybill ${waybill} update: ${status}.`;

    try {
        const response = await fetch('/api/send-sms', {
            method: 'POST',
            headers: getAuthHeaders(),   // ← JWT header, not localStorage
            body: JSON.stringify({ phone, message })
        });
        if (!isBulk) {
            const result = await response.json();
            if (response.status === 401) {
                // Token expired mid-session
                redirectToLogin('expired');
                return;
            }
            if (!result.success) showToast('SMS Gateway Rejected Number', 'warning');
        }
    } catch (e) {
        if (!isBulk) showToast('SMS Gateway Offline', 'warning');
    }
}


// ============================================================
// PATCHED handleLogout
// Calls server to invalidate JTI, then clears sessionStorage.
// Replace the existing handleLogout function in operations.html.
// ============================================================
window.handleLogout = async function() {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            headers: getAuthHeaders()
        });
    } catch (e) {
        // Even if server call fails, clear local session
        console.warn('[Logout] Server call failed, clearing local session');
    }
    Session.clear();
    redirectToLogin();
};


// ============================================================
// PATCHED unlockSystem
// Replaces the prompt() + localStorage block entirely.
// The token is already in sessionStorage from login.html.
// ============================================================
async function unlockSystem() {
    document.getElementById('killSwitchOverlay').style.display = 'none';
    document.getElementById('mainDashboardContent').classList.remove('hidden');
    document.getElementById('nodeIdentityDisplay').innerText =
        'ACTIVE NODE: ' + CONFIG.appId.toUpperCase();

    // No prompt() — credentials come from the verified session
    // Apply UI role gating before starting data sync
    injectSessionIndicator();
    applyRoleGating();
    startExpiryWatcher();
    startDataSync();
}


// ============================================================
// PATCHED runSecurityHandshake
// Adds session verification before the Firebase is_active check.
// ============================================================
async function runSecurityHandshake() {
    logDiagnostic('Identity', 'ok', CONFIG.appId);

    // ── STEP 0: Verify JWT session before anything else ──
    logDiagnostic('Session', 'wait', 'Verifying dispatcher credentials...');
    const sessionValid = await verifySessionOnLoad();
    if (!sessionValid) {
        // verifySessionOnLoad handles the redirect
        logDiagnostic('Session', 'fail', 'No valid session — redirecting');
        return;
    }
    logDiagnostic('Session', 'ok', `${Session.getDisplayName()} · ${Session.getRole()}`);

    // ── STEP 1: Firebase anonymous auth ──
    const dataPath = `artifacts/${CONFIG.appId}/public/data`;
    try {
        await auth.signInAnonymously();
        logDiagnostic('Auth', 'ok', 'Session Initialized');
    } catch (e) {
        logDiagnostic('Auth', 'wait', 'Domain Authorization Pending');
    }

    // ── STEP 2: is_active kill switch ──
    db.doc(dataPath).onSnapshot(doc => {
        if (!doc.exists) {
            logDiagnostic('Vault', 'fail', 'Data Document Not Found');
            showLockScreen('System Unidentified', `Document '${CONFIG.appId}' does not exist.`);
            return;
        }
        logDiagnostic('Vault', 'ok', 'Data Document Found');
        const data = doc.data();

        if (data.is_active !== true) {
            const reason = data.suspension_reason || 'Contact Ledgehold to complete onboarding.';
            logDiagnostic('Status', 'fail', 'PENDING ACTIVATION');
            showLockScreen('Access Pending Activation', reason);
        } else {
            logDiagnostic('Status', 'ok', 'ACCESS_GRANTED');
            unlockSystem();
        }
    }, err => {
        logDiagnostic('Vault', 'fail', 'Refused: Check Firebase Rules');
        console.error('Firebase Error:', err);
    });
}


// ============================================================
// BOOT
// ============================================================
// Replace window.onload in operations.html with this.
// This ensures the session check runs before Firebase initializes.
window.onload = runSecurityHandshake;