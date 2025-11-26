from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# Use 'os.environ.get' so you can use Render's safe environment variables later
# For now, you can paste your LIVE secret key here if you want.
PAYSTACK_SECRET_KEY = "sk_test_205609e95584b8704c90e2c8c72b6f1dbcee60db"

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
    # Your Price List
    pricing = {
        "mtn": [
            {"name": "5GB Non-Expiry", "price": 25}, # Set real prices now
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

# --- VERIFICATION ROUTE (Fast Version) ---
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
            # SUCCESS! Return immediately so the user sees the Thank You page.
            # We rely on Paystack to email YOU the receipt.
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "failed"})
            
    except Exception as e:
        print(f"Error connecting to Paystack: {e}")
        return jsonify({"status": "error"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)