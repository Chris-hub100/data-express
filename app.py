import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify # <--- ADDED request, jsonify
import requests # <--- ADDED requests (needed to talk to Paystack)

app = Flask(__name__)

# --- CONFIGURATION ---
# ⚠️ REPLACE THIS WITH YOUR LIVE SECRET KEY (Starts with sk_live_)
PAYSTACK_SECRET_KEY = "sk_test_205609e95584b8704c90e2c8c72b6f1dbcee60db"

EMAIL_SENDER = "tettehchris100@gmail.com"
EMAIL_PASSWORD = "uhfm zzbr jyrr lwun"
ADMIN_EMAIL = "tettehchris100@gmail.com"

# --- EMAIL LOGIC ---
def send_alert(order_details):
    try:
        subject = f"💰 NEW ORDER: {order_details['bundle']}"
        body = f"""
        NEW SALE ALERT!
        -------------------------
        Customer: {order_details['name']}
        Phone:    {order_details['phone']}
        Bundle:   {order_details['bundle']}
        Ref Code: {order_details['ref']}
        -------------------------
        ACTION REQUIRED:
        Send {order_details['bundle']} to {order_details['phone']} now.
        """

        msg = MIMEMultipart()
        msg['From'] = "DataExpress Bot"
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail Server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, ADMIN_EMAIL, text)
        server.quit()
        print("✅ Email Alert Sent!")
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/success')
def success_page():
    return render_template('success.html')

@app.route('/buy/<network>')
def product_page(network):
    pricing = {
        "mtn": [
            {"name": "5GB Non-Expiry", "price": 0.1}, # 10 Pesewas for testing
            {"name": "10GB Non-Expiry", "price": 45}
        ],
        "telecel": [
            {"name": "10GB Special", "price": 30},
            {"name": "20GB Special", "price": 55}
        ],
        "at": [
            {"name": "Big Time 5GB", "price": 15}
        ]
    }
    selected_bundles = pricing.get(network, [])
    return render_template('product.html', 
                           network_name=network.upper(), 
                           bundles=selected_bundles)


# --- THE FIXED VERIFICATION ROUTE ---
@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    data = request.json
    reference = data.get('reference')
    
    # 1. Ask Paystack: "Is this transaction real?"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    
    try:
        response = requests.get(url, headers=headers)
        json_resp = response.json()
        
        # 2. Check if Paystack says "success"
        if json_resp['status'] is True and json_resp['data']['status'] == "success":
            
            # 3. SUCCESS! 
            order_info = {
                "name": data['name'],
                "phone": data['phone'],
                "bundle": data['bundle'],
                "ref": reference
            }
            
            # --- THE FIX: RUN EMAIL IN BACKGROUND ---
            # We tell Python: "Do this email stuff later, don't block the user."
            email_thread = threading.Thread(target=send_alert, args=(order_info,))
            email_thread.start()
            
            # 4. Return success IMMEDIATELY to the frontend
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "failed"})
            
    except Exception as e:
        print(f"Error connecting to Paystack: {e}")
        return jsonify({"status": "error"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)