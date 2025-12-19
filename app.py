from flask import Flask, render_template, request, jsonify
import requests
import os
import random
import datetime
from datetime import date, timedelta

app = Flask(__name__)

# --- CONFIGURATION ---
# Use 'os.environ.get' for safety in production
PAYSTACK_SECRET_KEY = "sk_test_205609e95584b8704c90e2c8c72b6f1dbcee60db"

# --- HUBTEL COMPLIANCE SWITCH ---
# Set to TRUE while applying for Hubtel. 
# Set to FALSE once approved to unlock Movies & Vouchers.
COMPLIANCE_MODE = True

@app.route('/')
def home():
    # 1. Existing QR Code Logic
    source = request.args.get('ref')
    welcome_msg = None
    welcome_type = "info"

    if source == 'front':
        welcome_msg = "You just wasted your time and your data scanning this. Anyway, to help cover for your loss check out some of our amazing deals."
        welcome_type = "success"
    elif source == 'back':
        welcome_msg = "Nice catch! They say curiosity kills the cat but this time it rewards it. Go explore your rewards."
        welcome_type = "primary"
    elif source == 'tshirt':
        welcome_msg = "Hey Scholar! 👋 Check out our Student Specials below."
        welcome_type = "primary"

    # 2. Food Run Logic (Pass this to home.html if you want a 'Live' badge)
    today_idx = datetime.datetime.now().weekday() # 0=Mon, 4=Fri, 6=Sun
    food_is_active = today_idx >= 4

    return render_template('home.html', 
                         welcome_msg=welcome_msg, 
                         welcome_type=welcome_type,
                         food_active=food_is_active) # You can use {{ food_active }} in home.html now

@app.route('/healthz')
def health_check():
    return "OK", 200

@app.route('/foodrun')
def food_run_page():
    # Logic: Open Friday (4), Saturday (5), Sunday (6)
    today_idx = datetime.datetime.now().weekday()
    today_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][today_idx]
    
    if today_idx >= 4:
        state = "open"
        # The Menu
        menu = [
            {"item": "KFC Streetwise 2 (Rice)", "price": 45.00, "img": "🍗"},
            {"item": "Waakye Special (Egg + Fish)", "price": 30.00, "img": "🍛"},
            {"item": "Coke / Fanta (500ml)", "price": 10.00, "img": "🥤"}
        ]
    else:
        state = "closed"
        menu = []

    return render_template('foodrun.html', state=state, menu=menu, today_name=today_name, today_idx=today_idx)

@app.route('/quote')
def quote_page():
    return render_template('quote.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/success')
def success_page():
    return render_template('success.html')

@app.route('/terms')
def terms_page():
    return render_template('terms.html')

# --- TV / ENTERTAINMENT (HIDDEN IN COMPLIANCE MODE) ---
@app.route('/tv')
def tv_page():
    if COMPLIANCE_MODE:
        return render_template('maintenance.html', page_name="Entertainment Hub")

    # A. THE MOVIE POOL (From second code - complete list)
    movies = [
        {"id": "43R9l7EkJwE", "title": "Predator: Badlands", "creator": "20th Century", "type": "video"},
        {"id": "ZdC5mFHPldg", "title": "Mortal Kombat II", "creator": "Warner Bros", "type": "video"},
        {"id": "OpThntO9ixc", "title": "Weapons", "creator": "Warner Bros", "type": "video"},
        {"id": "8yh9BPUBbbQ", "title": "F1® The Movie", "creator": "Warner Bros", "type": "video"},
        {"id": "-E3lMRx7HRQ", "title": "Now You See Me 3", "creator": "Lionsgate", "type": "video"},
        {"id": "DCWcK4c-F8Q", "title": "The Amateur", "creator": "20th Century", "type": "video"},
        {"id": "vEioDeOiqEs", "title": "Murderbot", "creator": "Apple TV", "type": "video"},
        {"id": "bMgfsdYoEEo", "title": "The Conjuring: Last Rites", "creator": "Warner Bros", "type": "video"},
        {"id": "dqolYtJGuf4", "title": "The Family Plan 2", "creator": "Apple TV", "type": "video"},
        {"id": "AuYmKbtnmEA", "title": "Michael", "creator": "Universal", "type": "video"},
        {"id": "5r-7eWDBc40", "title": "GOAT", "creator": "Sony Pictures", "type": "video"},
        {"id": "tA1s65o_kYM", "title": "Mickey 17", "creator": "Warner Bros", "type": "video"},
        {"id": "lMXh6vjiZrI", "title": "Mufasa: The Lion King", "creator": "Disney", "type": "video"},
        {"id": "1pHDWnXmK7Y", "title": "Captain America 4", "creator": "Marvel", "type": "video"},
        {"id": "lQBmZBJCYcY", "title": "Squid Game Season 2", "creator": "Netflix", "type": "video"},
        {"id": "dSDpoobO6yM", "title": "Five Nights at Freddy's 2", "creator": "Universal", "type": "video"},
        {"id": "az8M5Mai0X4", "title": "Anaconda", "creator": "Sony Pictures", "type": "video"},
        {"id": "EOwTdTZA8D8", "title": "28 Years Later", "creator": "Sony Pictures", "type": "video"},
        {"id": "n0pqP6ClcE8", "title": "Rental Family", "creator": "Searchlight", "type": "video"},
        {"id": "R4wiXj9NmEE", "title": "Send Help", "creator": "20th Century", "type": "video"},
        {"id": "zHhR3daI3bY", "title": "Man Vs Baby", "creator": "Netflix", "type": "video"},
        {"id": "m3lgD59KrTw", "title": "Hedda", "creator": "Prime Video", "type": "video"},
        {"id": "Hzk4ovnGOyw", "title": "Troll 2", "creator": "Netflix", "type": "video"},
        {"id": "8seUGDLZRIo", "title": "Swiped", "creator": "Hulu", "type": "video"},
        {"id": "vAtUHeMQ1F8", "title": "The Long Walk", "creator": "Lionsgate Movies", "type": "video"},
        {"id": "M7LhGytiHFM", "title": "Shadow Force", "creator": "Lionsgate Movies", "type": "video"},
        {"id": "o34WOE1a8aQ", "title": "Good Fortune", "creator": "Lionsgate Movies", "type": "video"},
        {"id": "moiRCJR4ToY", "title": "The Blackening", "creator": "Lionsgate Movies", "type": "video"},
        {"id": "H8ieN10lX40", "title": "Greenland 2", "creator": "Lionsgate Movies", "type": "video"},
        {"id": "U9OkHjOnQPg", "title": "She Rides Shotgun", "creator": "Lionsgate Movies", "type": "video"},
        {"id": "k_8YOQ0TMfM", "title": "Turbulence", "creator": "Lionsgate Movies", "type": "video"},
        {"id": "_wpw2QHJNco", "title": "A House Of Dynamite", "creator": "Netflix", "type": "video"},
        {"id": "MPjxijuBuSo", "title": "The Hunger Games: Sunrise on the Reaping", "creator": "Lionsgate Movies", "type": "video"},
        {"id": "f5y-cziwmMw", "title": "Crime 101", "creator": "Amazon MGM Studios", "type": "video"},
        {"id": "KD18ddeFuyM", "title": "The Running Man", "creator": "Paramount Pictures", "type": "video"},
        {"id": "i36Zw32GfRQ", "title": "Reminders of Him", "creator": "Universal Pictures", "type": "video"},
        {"id": "kr3wIXhmYpI", "title": "Strays", "creator": "Universal Pictures", "type": "video"},
        {"id": "YShVEXb7-ic", "title": "Tron: Ares", "creator": "Disney", "type": "video"},
        {"id": "IHikM7vFXsA", "title": "Roofman", "creator": "Paramount Pictures", "type": "video"},
        {"id": "ZsAa9ofaL-g", "title": "Red Alert", "creator": "Paramount Plus", "type": "video"},
        {"id": "z1xJAyVKAPY", "title": "The Black Demon", "creator": "Paramount Movies", "type": "video"},
        {"id": "nfKO9rYDmE8", "title": "The Lost City", "creator": "Paramount Pictures", "type": "video"},
        {"id": "R6W6YzhRuTA", "title": "SHELL", "creator": "Paramount Movies", "type": "video"}
    ]

    random.shuffle(movies)

    # ADS - Only add Stake ads when NOT in compliance mode
    if not COMPLIANCE_MODE:
        ad_1 = {
            "type": "ad",
            "title": "Win like Drake with Stake",
            "desc": "Instant Withdrawals via MoMo or Crypto. 200% Bonus.",
            "link": "https://stake.com/?c=TqdL9FFw",
            "image": "/static/images/stake-logo-navy.png"
        }
        
        ad_2 = {
            "type": "ad",
            "title": "Sign up today, it may be your lucky day",
            "desc": "The world's biggest crypto casino. Play now.",
            "link": "https://stake.com/?c=TqdL9FFw",
            "image": "/static/images/stake com-logo-navy.png"
        }

        ad_3 = {
            "type": "ad",
            "title": "Stake and Win",
            "desc": "Join the winning team. 200% Deposit Match.",
            "link": "https://stake.com/?c=TqdL9FFw",
            "image": "/static/images/stake-logo-navy.png"
        }

        # INJECT ADS AT FIXED POSITIONS (From second code)
        # Insert from last to first to avoid messing up the index order
        if len(movies) > 41: movies.insert(41, ad_3)
        if len(movies) > 32: movies.insert(32, ad_2)
        if len(movies) > 25: movies.insert(25, ad_1)
        if len(movies) > 16: movies.insert(16, ad_3)
        if len(movies) > 8: movies.insert(8, ad_2)
        if len(movies) > 3: movies.insert(3, ad_1)
    
    return render_template('tv.html', videos=movies)

# --- VOUCHERS (HIDDEN IN COMPLIANCE MODE) ---
@app.route('/vouchers')
def voucher_page():
    if COMPLIANCE_MODE:
        return render_template('maintenance.html', page_name="Voucher Mall")

    # From second code - complete voucher list
    items = [
        {
            "name": "Audiomack",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiJlOTVlM2NjOC0zNWYwLTQ5MjctOWM3MS0yMTRlN2ZiYzVmOTgucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjc2OH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "audiomack",
            "desc": "Subscription"
        },
        {
            "name": "Tinder",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiI5ZGQxOGRhYy0wN2E4LTQ3NTctYTQ5NC04YzU5MmNjYjE5M2UucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjM4NH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "tinder",
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
            "link": "codm",
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
            "link": "codm.",
            "desc": "Battle Pass"
        },
        {
            "name": "Marvel Rivals",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiIxMDRlYjFmNi1kMThiLTRjNGItODU4OS1iMWJiYjRiMzc4NzQucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjM4NH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "marvelrivals",
            "desc": "Lattices"
        },
        {
            "name": "Delta Force",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiIyYTVjYzFiYy00Yjg4LTQ2ZmYtYmFiZi04MTc3M2NkYTA1YTIucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjM4NH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "deltaforce",
            "desc": "Coins"
        },
        {
            "name": "Honor of Kings",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiIzZmJhZTU0Mi1iZTM0LTRjM2EtYmM1Yy0xYTE4NzYxOGU0NzMucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjM4NH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "honorofkings",
            "desc": "Tokens"
        },
        {
            "name": "Arena Breakout",
            "image": "https://d13ms5efar3wc5.cloudfront.net/eyJidWNrZXQiOiJpbWFnZXMtY2Fycnkxc3QtcHJvZHVjdHMiLCJrZXkiOiJmZTY2NTRjYy00YzEyLTQ5NWEtOGMzMi1kNjhiNDMwOTkwYjgucG5nLndlYnAiLCJlZGl0cyI6eyJyZXNpemUiOnsid2lkdGgiOjM4NH19LCJ3ZWJwIjp7InF1YWxpdHkiOjc1fX0=",
            "link": "arenabreakout",
            "desc": "Bonds"
        }
    ]
    return render_template('vouchers.html', items=items)

# --- UNIVERSAL BUY PAGE ---
@app.route('/buy/<network>')
def product_page(network):
    # If in Compliance Mode, BLOCK voucher networks
    risky_networks = ['audiomack', 'tinder', 'fcmobile', 'freefire', 'codm', 'marvelrivals', 'deltaforce', 'honorofkings', 'arenabreakout', 'fcmobile.', 'codm.']
    
    if COMPLIANCE_MODE and network in risky_networks:
        return render_template('maintenance.html', page_name="Digital Vouchers")

    # MASTER PRICE LIST (From second code - complete pricing)
    pricing = {
        # --- DATA BUNDLES (Keep these active for 'Campus Connectivity') ---
        "mtn": [
            {"name": "1GB Non-Expiry", "price": 5.5, "input_type": "phone", "active": True}, 
            {"name": "2GB Non-Expiry", "price": 10.5, "input_type": "phone", "active": True},
            {"name": "3GB Non-Expiry", "price": 15, "input_type": "phone", "active": True},
            {"name": "4GB Non-Expiry", "price": 20, "input_type": "phone", "active": True},
            {"name": "5GB Non-Expiry", "price": 25, "input_type": "phone", "active": True },
            {"name": "6GB Non-Expiry", "price": 28, "input_type": "phone", "active": True},
            {"name": "8GB Non-Expiry", "price": 37, "input_type": "phone", "active": True},
            {"name": "10GB Non-Expiry", "price": 46, "input_type": "phone", "active": True},
            {"name": "15GB Non-Expiry", "price": 66, "input_type": "phone", "active": True},
            {"name": "20GB Non-Expiry", "price": 88, "input_type": "phone", "active": True},
            {"name": "30GB Non-Expiry", "price": 132, "input_type": "phone", "active": True},
            {"name": "40GB Non-Expiry", "price": 180, "input_type": "phone", "active": True},
            {"name": "50GB Non-Expiry", "price": 215, "input_type": "phone", "active": True},
            {"name": "100GB Non-Expiry", "price": 430, "input_type": "phone", "active": True},
        ],
        "telecel": [
            {"name": "10GB Special", "price": 40, "input_type": "phone", "active": True},
            {"name": "15GB Special", "price": 60, "input_type": "phone", "active": True},
            {"name": "20GB Non-Expiry", "price": 90, "input_type": "phone", "active": True},
            {"name": "25GB Non-Expiry", "price": 120, "input_type": "phone", "active": True},
            {"name": "30GB Non-Expiry", "price": 130, "input_type": "phone", "active": True},
            {"name": "40GB Non-Expiry", "price": 160, "input_type": "phone", "active": True},
            {"name": "50GB Non-Expiry", "price": 200, "input_type": "phone", "active": True},
            {"name": "100GB Non-Expiry", "price": 380, "input_type": "phone", "active": True},
        ],
        "at": [
            {"name": "1GB Non-Expiry", "price": 5, "input_type": "phone", "active": True},
            {"name": "3GB Non-Expiry", "price": 13, "input_type": "phone", "active": True},
            {"name": "4GB Non-Expiry", "price": 18, "input_type": "phone", "active": True},
            {"name": "5GB Non-Expiry", "price": 23, "input_type": "phone", "active": True},
            {"name": "8GB Non-Expiry", "price": 35, "input_type": "phone", "active": True},
            {"name": "10GB Non-Expiry", "price": 45, "input_type": "phone", "active": True},
            {"name": "12GB Non-Expiry", "price": 53, "input_type": "phone", "active": True},
        ],

        # --- VOUCHERS (These are blocked in COMPLIANCE_MODE) ---
        "audiomack": [
            {"name": "Audiomack Day Pass", "price": 3, "input_type": "email", "active": True},
            {"name": "Audiomack Monthly Pass", "price": 25, "input_type": "email", "active": True}
        ],
         "tinder": [
            {"name": "Standard 1 Week - Plus", "price":25, "input_type": "phone", "active": True},
            {"name": "Standard 1 Week - Gold", "price": 35, "input_type": "phone", "active": True},
            {"name": "Standard 1 Month - Plus", "price": 42, "input_type": "phone", "active": True},
            {"name": "Standard 1 Month - Gold", "price": 55, "input_type": "phone", "active": True},
        ],
        "fcmobile": [
            {"name": "40 FC Points", "price": 7, "input_type": "id", "active": True},
            {"name": "100 FC Points", "price": 17, "input_type": "id", "active": True},
            {"name": "520 FC Points", "price": 80, "input_type": "id", "active": True},
            {"name": "1070 FC Points", "price": 160, "input_type": "id", "active": True},
            {"name": "2200 FC Points", "price": 310, "input_type": "id", "active": True},
            {"name": "5750 FC Points", "price": 775, "input_type": "id", "active": True},
            {"name": "12000 FC Points", "price": 1570, "input_type": "id", "active": True},
        ],
        "freefire": [
            {"name": "100 Diamonds", "price": 18, "input_type": "id", "active": True},
            {"name": "210 Diamonds", "price": 32, "input_type": "id", "active": True},
            {"name": "530 Diamonds", "price": 72, "input_type": "id", "active": True},
            {"name": "1080 Diamonds", "price": 142, "input_type": "id", "active": True},
            {"name": "2200 Diamonds", "price": 275, "input_type": "id", "active": True},
        ],
        "codm": [
            {"name": "880 CP", "price": 145, "input_type": "id", "active": True},
            {"name": "30 CP", "price": 7, "input_type": "id", "active": True},
            {"name": "80 CP", "price": 15, "input_type": "id", "active": True},
            {"name": "420 CP", "price": 72, "input_type": "id", "active": True},
            {"name": "2400 CP", "price": 370, "input_type": "id", "active": True},
            {"name": "5000 CP", "price": 730, "input_type": "id", "active": True},
            {"name": "10800 CP", "price": 1440, "input_type": "id", "active": True},
            {"name": "21600 CP", "price": 2600, "input_type": "id", "active": True},
            {"name": "32400 CP", "price": 3800, "input_type": "id", "active": True},
            {"name": "54000 CP", "price": 6200, "input_type": "id", "active": True}
        ],
        "fcmobile.": [
            {"name": "39 Silver", "price": 8, "input_type": "id", "active": True},
            {"name": "99 Silver", "price": 18, "input_type": "id", "active": True},
            {"name": "499 Silver", "price": 82, "input_type": "id", "active": True},
            {"name": "1999 Silver", "price": 317, "input_type": "id", "active": True},
            {"name": "4999 Silver", "price": 780, "input_type": "id", "active": True},
            {"name": "9999 Silver", "price": 1550, "input_type": "id", "active": True},
        ],
        "codm.": [
            {"name": "Battle Pass Premium", "price": 40, "input_type": "id", "active": True},
            {"name": "Battle Pass Premium Bundle", "price": 93, "input_type": "id", "active": True}
        ],
         "marvelrivals": [
            {"name": "100 Lattices", "price": 15, "input_type": "id", "active": True},
            {"name": "500 Lattices", "price": 70, "input_type": "id", "active": True},
            {"name": "1000 Lattices", "price": 142, "input_type": "id", "active": True},
            {"name": "2180 Lattices", "price": 283, "input_type": "id", "active": True},
            {"name": "5680 Lattices", "price": 660, "input_type": "id", "active": True},
            {"name": "11680 Lattices", "price": 1310, "input_type": "id", "active": True},
        ],
        "deltaforce": [
            {"name": "18 Delta Coins", "price": 5.5, "input_type": "id", "active": True},
            {"name": "30 Delta Coins", "price": 9, "input_type": "id", "active": True},
            {"name": "60 Delta Coins", "price": 14, "input_type": "id", "active": True},
            {"name": "320 Delta Coins", "price": 60, "input_type": "id", "active": True},
            {"name": "460 Delta Coins", "price": 82, "input_type": "id", "active": True},
            {"name": "750 Delta Coins", "price": 115, "input_type": "id", "active": True},
        ],
        "honorofkings": [
            {"name": "16 Tokens", "price": 5, "input_type": "id", "active": True},
            {"name": "80 Tokens", "price": 15, "input_type": "id", "active": True},
            {"name": "240 Tokens", "price": 40, "input_type": "id", "active": True},
            {"name": "400 Tokens", "price": 65, "input_type": "id", "active": True},
            {"name": "560 Tokens", "price": 90, "input_type": "id", "active": True},
            {"name": "830 Tokens", "price": 130, "input_type": "id", "active": True},
        ],
        "arenabreakout": [
            {"name": "66 Bonds", "price": 15, "input_type": "id", "active": True},
            {"name": "335 Bonds", "price": 66, "input_type": "id", "active": True},
            {"name": "675 Bonds", "price": 130, "input_type": "id", "active": True},
            {"name": "1690 Bonds", "price": 317, "input_type": "id", "active": True},
            {"name": "3400 Bonds", "price": 630, "input_type": "id", "active": True},
            {"name": "6820 Bonds", "price": 1255, "input_type": "id", "active": True},
        ]
    }
    
    selected_bundles = pricing.get(network, [])
    data_networks = ['mtn', 'telecel', 'at']
    is_voucher = network not in data_networks
    
    # Fallback to 'phone' if empty
    input_type = selected_bundles[0]['input_type'] if selected_bundles else 'phone'
    
    return render_template('product.html', 
                           network_name=network.upper(), 
                           bundles=selected_bundles,
                           input_type=input_type,
                           is_voucher=is_voucher)

# --- PAYMENT VERIFICATION ---
@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    data = request.json
    reference = data.get('reference')
    
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    
    try:
        response = requests.get(url, headers=headers)
        json_resp = response.json()
        
        if json_resp['status'] is True and json_resp['data']['status'] == "success":
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "failed"})
            
    except Exception as e:
        print(f"Error connecting to Paystack: {e}")
        return jsonify({"status": "error"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)