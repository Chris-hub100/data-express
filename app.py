from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# Use 'os.environ.get' so you can use Render's safe environment variables later
# For now, you can paste your LIVE secret key here if you want.
PAYSTACK_SECRET_KEY = "sk_test_205609e95584b8704c90e2c8c72b6f1dbcee60db"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/success')
def success_page():
    return render_template('success.html')

# --- 1. THE CINEMA PAGE (YouTube Movie Trailers) ---
@app.route('/tv')
def tv_page():
    # Official Movie Trailers (2025 Blockbusters)
    videos = [
        {
            "id": "lMXh6vjiZrI",  # Mufasa: The Lion King (Disney)
            "title": "Mufasa: The Lion King",
            "creator": "Disney"
        },
        {
            "id": "1pHDWnXmK7Y",  # Captain America: Brave New World (Marvel)
            "title": "Captain America 4",
            "creator": "Marvel Studios"
        },
        {
            "id": "lQBmZBJCYcY",  # Squid Game Season 2 (Netflix)
            "title": "Squid Game Season 2",
            "creator": "Netflix"
        },
        {
            "id": "dSDpoobO6yM", # Five Nights at Freddy's (Universal)
            "title": "Five Nights at Freddy's",
            "creator": "Universal Pictures"
        },
        {
            "id": "az8M5Mai0X4", # Anaconda (Sony)
            "title": "Anaconda",
            "creator": "Sony Pictures"
        },
        {
            "id": "EOwTdTZA8D8", # 28 Years Later (Sony)
            "title": "28 Years Later",
            "creator": "Sony Pictures"
        },
        {
            "id": "n0pqP6ClcE8", # Rental Family (Searchlight)
            "title": "Rental Family",
            "creator": "Searchlight Pictures"
        },
        {
            "id": "R4wiXj9NmEE", # Send Help (20th Century)
            "title": "Send Help",
            "creator": "20th Century Studios"
        }
    ]
    return render_template('tv.html', videos=videos)

# --- 2. THE VOUCHER MALL (Gift Cards Page) ---
@app.route('/vouchers')
def voucher_page():
    items = [
        {
            "name": "Audiomack",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiJlOTVlM2NjOC0zNWYwLTQ5MjctOWM3MS0yMTRlN2ZiYzVmOTgucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjc2OH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "audiomack",
            "desc": "Subscription"
        },
        {
            "name": "EA Sports FC™ Mobile",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiIyNWNlMjI5Yi00YmQ3LTRjMTktOGE4Yy0zOTY5MzNiMmE5NDMucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjc2OH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "fcmobile",
            "desc": "FC Points"
        },
        {
            "name": "Free Fire",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiIwNDUzOTRmOC0zMWY1LTRlMDMtYjQ1OS03ZWEzMmJlZWY1YjQucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjM4NH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "freefire",
            "desc": "Diamonds"
        },
        {
            "name": "Call of Duty: Mobile",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiI4NmYyM2EwNi00MjI4LTQyNzctOTQwMS00ZWVlZTBkY2NmMzgucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjc2OH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "cod",
            "desc": "COD Points"
        },
        {
            "name": "EA Sports FC™ Mobile",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiIyNWNlMjI5Yi00YmQ3LTRjMTktOGE4Yy0zOTY5MzNiMmE5NDMucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjM4NH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "fcmobile.",
            "desc": "Silver"
        },
        {
            "name": "Call of Duty: Mobile",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiI4NmYyM2EwNi00MjI4LTQyNzctOTQwMS00ZWVlZTBkY2NmMzgucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjM4NH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "cod.",
            "desc": "Battle Pass"
        }
    ]
    return render_template('vouchers.html', items=items)

# --- 3. THE UNIVERSAL BUY PAGE (Handles Data + Vouchers) ---
@app.route('/buy/<network>')
def product_page(network):
    # MASTER PRICE LIST
    pricing = {
        # --- DATA BUNDLES ---
        "mtn": [
            {"name": "5GB Non-Expiry", "price": 25, "input_type": "phone"}, 
            {"name": "10GB Non-Expiry", "price": 45, "input_type": "phone"}
        ],
        "telecel": [
            {"name": "10GB Special", "price": 30, "input_type": "phone"},
            {"name": "20GB Special", "price": 55, "input_type": "phone"}
        ],
        "at": [
            {"name": "Big Time 5GB", "price": 15, "input_type": "phone"}
        ],

        # --- VOUCHERS ---
        "audiomack": [
            {"name": "Audiomack Day Pass", "price": 3, "input_type": "phone"},
            {"name": "Audiomack Monthly Pass", "price": 25, "input_type": "phone"}
        ],
        "fcmobile": [
            {"name": "40 FC Points", "price": 7, "input_type": "id"},
            {"name": "100 FC Points", "price": 17, "input_type": "id"},
            {"name": "520 FC Points", "price": 80, "input_type": "id"},
            {"name": "1070 FC Points", "price": 160, "input_type": "id"},
            {"name": "2200 FC Points", "price": 310, "input_type": "id"},
            {"name": "5750 FC Points", "price": 775, "input_type": "id"},
            {"name": "12000 FC Points", "price": 1570, "input_type": "id"},
        ],
        "freefire": [
            {"name": "100 Diamonds", "price": 18, "input_type": "id"},
            {"name": "210 Diamonds", "price": 32, "input_type": "id"},
            {"name": "530 Diamonds", "price": 72, "input_type": "id"},
            {"name": "1080 Diamonds", "price": 142, "input_type": "id"},
            {"name": "2200 Diamonds", "price": 275, "input_type": "id"},
        ],
        "cod": [
            {"name": "880 CP", "price": 145, "input_type": "id"},
            {"name": "30 CP", "price": 7, "input_type": "id"},
            {"name": "80 CP", "price": 15, "input_type": "id"},
            {"name": "420 CP", "price": 72, "input_type": "id"},
            {"name": "2400 CP", "price": 370, "input_type": "id"},
            {"name": "5000 CP", "price": 730, "input_type": "id"},
            {"name": "10800 CP", "price": 1440, "input_type": "id"},
            {"name": "21600 CP", "price": 2600, "input_type": "id"},
            {"name": "32400 CP", "price": 3800, "input_type": "id"},
            {"name": "54000 CP", "price": 6200, "input_type": "id"}
        ],
        "fcmobile.": [
            {"name": "39 Silver", "price": 8, "input_type": "id"},
            {"name": "99 Silver", "price": 18, "input_type": "id"},
            {"name": "499 Silver", "price": 82, "input_type": "id"},
            {"name": "1999 Silver", "price": 317, "input_type": "id"},
            {"name": "4999 Silver", "price": 780, "input_type": "id"},
            {"name": "9999 Silver", "price": 1550, "input_type": "id"},
        ],
        "kaspersky": [
            {"name": "Battle Pass Premium", "price": 40, "input_type": "id"},
            {"name": "Battle Pass Premium Bundle", "price": 93, "input_type": "id"}
        ]
    }
    
    selected_bundles = pricing.get(network, [])#

    data_networks = ['mtn', 'telecel', 'at']
    
    # Check if this is a voucher (to change "MoMo Number" to "WhatsApp Number" in HTML)
    #voucher_list = ['showmax', 'netflix', 'freefire', 'pubg', 'playstation', 'kaspersky']
    is_voucher = network not in data_networks
    
    input_type = selected_bundles[0]['input_type'] if selected_bundles else 'phone'
    
    return render_template('product.html', 
                           network_name=network.upper(), 
                           bundles=selected_bundles,
                           input_type=input_type,
                           is_voucher=is_voucher)

# --- 4. PAYMENT VERIFICATION ---
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
    # host='0.0.0.0' allows you to test on your phone via Wi-Fi
    app.run(host='0.0.0.0', port=5000, debug=True)