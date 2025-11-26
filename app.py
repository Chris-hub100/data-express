import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template

app = Flask(__name__)

# --- CONFIGURATION ---
EMAIL_SENDER = "tettehchris100@gmail.com"  # <--- PUT YOUR GMAIL HERE
EMAIL_PASSWORD = "uhfm zzbr jyrr lwun" # <--- PUT YOUR 16-LETTER APP PASSWORD HERE
ADMIN_EMAIL = "tettehchris100@gmail.com"   # <--- Where should the alert go? (Your phone)

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
        server.starttls() # Secure the connection
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, ADMIN_EMAIL, text)
        server.quit()
        print("✅ Email Alert Sent!")
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# 1. LANDING PAGE
@app.route('/')
def home():
    return render_template('home.html') # Create a simple welcome page

# 2. SHOP PAGE ( The Grid)
@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/success')
def success_page():
    return render_template('success.html')

# 3. DYNAMIC PRODUCT PAGE
@app.route('/buy/<network>')
def product_page(network):
    # This acts like a database of your prices
    pricing = {
        "mtn": [
            {"name": "5GB Non-Expiry", "price": 0.1},
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

    
    # Get the bundles for the clicked network (or return empty if not found)
    selected_bundles = pricing.get(network, [])
    
    return render_template('product.html', 
                           network_name=network.upper(), 
                           bundles=selected_bundles)

if __name__ == '__main__':
    # host='0.0.0.0' means "Open to the network"
    app.run(host='0.0.0.0', port=5000, debug=True)