import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, redirect, render_template_string, session, url_for

user_app = Flask('user_app')
app = user_app
user_app.secret_key = os.environ.get('SECRET_KEY', 'b4u_empire_shadow_sovereign_gate_2026')

DB_FILE = "/tmp/database.db"

SEED_USERS = [
    ("B4U1001", "Ahsan Farooqi", "admin", "Tiffany", 1000.0, 85.03, 500.0, "Active", None),
    ("B4U1002", "Naveed Ahmed Khan", "112233", "Tiffany", 0.0, 0.0, 0.0, "Active", "B4U1001"),
    ("B4U1003", "Niaz Ahmed", "Niaz123$$", "Tiffany", 10.0, 2.89, 50.0, "Active", "B4U1001"),
    ("B4U1004", "Checcking id", "112233", "Tiffany", 20.0, 5.0, 0.0, "Active", "B4U1003"),
    ("B4U1005", "B4U1003", "112233", "Tiffany", 40.0, 10.0, 15.0, "Active", "B4U1003"),
    ("B4U1006", "arham habib", "112233", "Tiffany", 500.0, 85.0, 200.0, "Active", "B4U1001"),
    ("B4U1007", "Shahyar", "786121", "Tiffany", 400.0, 68.0, 100.0, "Active", "B4U1001"),
    ("B4U1008", "Muhammadliaqatali", "555500", "Tiffany", 50.0, 8.5, 25.0, "Active", "B4U1001")
]

SEED_WITHDRAWALS = [
    ("B4U1001", 30.0, "EasyPaisa Personal Account", "03056610136", "✅ Approved"),
    ("B4U1001", 30.0, "EasyPaisa Personal Account", "03056610136", "✅ Approved"),
    ("B4U1001", 50.0, "EasyPaisa Personal Account", "03056610136", "✅ Approved"),
    ("B4U1001", 20.0, "EasyPaisa Personal Account", "03056610136", "✅ Approved"),
    ("B4U1001", 70.0, "EasyPaisa Personal Account", "03056610136", "⏳ Pending Liquidation")
]

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT UNIQUE,
            name TEXT,
            password TEXT,
            rank TEXT DEFAULT 'Tiffany',
            inv REAL DEFAULT 0.0,
            profit_wallet REAL DEFAULT 0.0,
            p2p_wallet REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Active',
            referrer TEXT,
            created_at TEXT
        )""")
        cols = [col[1] for col in conn.execute("PRAGMA table_info(users)").fetchall()]
        if 'p2p_wallet' not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN p2p_wallet REAL DEFAULT 0.0")

        conn.execute("""CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT,
            amount REAL,
            method TEXT,
            status TEXT DEFAULT '⏳ Pending Verification',
            created_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT,
            amount REAL,
            method TEXT,
            address TEXT,
            status TEXT DEFAULT '⏳ Pending Approval',
            created_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS p2p_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            recipient TEXT,
            amount REAL,
            created_at TEXT
        )""")

        user_count = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
        if user_count == 0:
            for uid, name, pwd, rank, inv, profit, p2p_w, status, referrer in SEED_USERS:
                conn.execute(
                    "INSERT INTO users (uid, name, password, rank, inv, profit_wallet, p2p_wallet, status, referrer, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (uid, name, generate_password_hash(pwd), rank, inv, profit, p2p_w, status, referrer, datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
                )
            for uid, amt, method, addr, status in SEED_WITHDRAWALS:
                conn.execute(
                    "INSERT INTO withdrawals (uid, amount, method, address, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (uid, amt, method, addr, status, datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
                )
            conn.execute(
                "INSERT INTO p2p_transfers (sender, recipient, amount, created_at) VALUES ('B4U1001', 'B4U1003', 100.0, ?)",
                (datetime.utcnow().strftime("%Y-%m-%d %H:%M"),)
            )
            conn.commit()

@app.before_request
def setup_db():
    init_db()

def generate_next_uid():
    with get_db() as conn:
        row = conn.execute("SELECT uid FROM users ORDER BY id DESC LIMIT 1").fetchone()
        if row and row['uid'].startswith("B4U"):
            last_num = int(row['uid'].replace("B4U", ""))
            return f"B4U{last_num + 1}"
        return "B4U1001"

def calculate_team_investment(uid):
    total = 0.0
    with get_db() as conn:
        refs = conn.execute("SELECT uid, inv FROM users WHERE referrer = ?", (uid,)).fetchall()
        for ref in refs:
            total += float(ref['inv'] or 0.0)
            total += calculate_team_investment(ref['uid'])
    return total

def get_downline_tree(uid, level=1):
    tree = []
    with get_db() as conn:
        refs = conn.execute("SELECT uid, name, inv, rank, status, created_at FROM users WHERE referrer = ?", (uid,)).fetchall()
        for ref in refs:
            member = dict(ref)
            member['level'] = level
            tree.append(member)
            tree.extend(get_downline_tree(ref['uid'], level + 1))
    return tree

def get_coin_price():
    with get_db() as conn:
        res = conn.execute("SELECT SUM(inv) as total FROM users").fetchone()
        total_inv = float(res['total'] or 0.0) if res else 0.0
        base_price = 1.00
        price_growth = (total_inv / 1000.0) * 0.05
        coin_price = round(base_price + price_growth, 4)
        coin_change = round(((coin_price - base_price) / base_price) * 100, 2)
        btc_usd = 68500.0
        b4u_in_btc = f"{coin_price / btc_usd:.8f}"
    return coin_price, coin_change, total_inv, btc_usd, b4u_in_btc

COIN_FAVICON = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='%23fdb913'/><circle cx='50' cy='50' r='40' fill='%232b1442'/><text x='50%' y='55%' dominant-baseline='middle' text-anchor='middle' fill='%23fdb913' font-family='sans-serif' font-weight='900' font-size='30'>$</text></svg>"
BIG_COIN_SVG = """<div style="position: relative; display: inline-block;"><div style="position: absolute; width: 100px; height: 100px; background: radial-gradient(circle, rgba(253,185,19,0.4) 0%, rgba(43,20,66,0) 70%); border-radius: 50%; top:-10px; left:-10px; animation: pulse 2s infinite alternate;"></div><svg width="85" height="85" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0px 0px 15px rgba(253, 185, 19, 0.8));"><defs><linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffe259" /><stop offset="100%" stop-color="#ffa751" /></linearGradient><linearGradient id="purpleBg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#3c1b5d" /><stop offset="100%" stop-color="#180729" /></linearGradient></defs><circle cx="50" cy="50" r="48" fill="url(#goldGrad)" stroke="#fff" stroke-width="2"/><circle cx="50" cy="50" r="40" fill="url(#purpleBg)" stroke="#fdb913" stroke-width="2"/><text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle" fill="#fdb913" font-family="'Segoe UI', sans-serif" font-weight="900" font-size="34">$</text><text x="50%" y="73%" dominant-baseline="middle" text-anchor="middle" fill="#ffffff" font-family="'Segoe UI', sans-serif" font-weight="900" font-size="10" letter-spacing="1.5">B4U</text></svg></div>"""
SMALL_COIN_SVG = """<svg width="32" height="32" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="48" fill="#fdb913"/><circle cx="50" cy="50" r="40" fill="#2b1442"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="#fdb913" font-family="sans-serif" font-weight="900" font-size="30">$</text></svg>"""

USER_LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>MEMBER PORTAL - B4U NETWORK</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>body { background: radial-gradient(circle at center, #240d38 0%, #10041a 100%); color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }.login-card { background: rgba(35, 13, 56, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(253, 185, 19, 0.3); border-top: 5px solid #fdb913; padding: 40px 35px; border-radius: 20px; width: 340px; box-shadow: 0 20px 40px rgba(0,0,0,0.7); text-align: center; }h2 { color: #fdb913; font-size: 20px; margin-top: 15px; font-weight: 800; letter-spacing: 1px; margin-bottom: 25px; text-shadow: 0 0 10px rgba(253,185,19,0.3); }input { width: 100%; padding: 12px; background: #130620; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 18px; box-sizing: border-box; outline:none; font-size:14px; }input:focus { border-color: #fdb913; box-shadow: 0 0 12px rgba(253, 185, 19, 0.4); }button { width: 100%; padding: 12px; background: linear-gradient(135deg, #fdb913, #e28700); border: none; font-weight: bold; cursor: pointer; border-radius: 8px; color: #1a0928; font-size: 15px; letter-spacing:1px; transition: 0.3s; }button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(253, 185, 19, 0.5); }.err { color: #ff4d4d; font-size: 13px; margin-bottom: 15px; background: rgba(255,77,77,0.1); padding: 8px; border-radius: 6px; border: 1px solid rgba(255,77,77,0.2); }.msg { color: #10b981; font-size: 13px; margin-bottom: 15px; background: rgba(16,185,129,0.1); padding: 8px; border-radius: 6px; border: 1px solid rgba(16,185,129,0.2); }.switch-link { color: #a78bfa; font-size: 13px; margin-top: 15px; display: block; text-decoration: none; }</style></head><body><div class="login-card">""" + BIG_COIN_SVG + """<h2>B4U MEMBER PORTAL</h2>{% if error %}<div class="err">{{ error }}</div>{% endif %}{% if msg %}<div class="msg">{{ msg }}</div>{% endif %}<form action="/login" method="POST"><input type="text" name="uid" placeholder="Node UID (e.g. B4U1001)" required><input type="password" name="password" placeholder="Access Key" required><button type="submit">LOGIN TO NETWORK</button></form><a href="/register" class="switch-link">Don't have an account? Register Here</a></div></body></html>"""

USER_REGISTER_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>REGISTER - B4U NETWORK</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>body { background: radial-gradient(circle at center, #240d38 0%, #10041a 100%); color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }.login-card { background: rgba(35, 13, 56, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(16, 185, 129, 0.3); border-top: 5px solid #10b981; padding: 40px 35px; border-radius: 20px; width: 340px; box-shadow: 0 20px 40px rgba(0,0,0,0.7); text-align: center; }h2 { color: #10b981; font-size: 20px; margin-top: 15px; font-weight: 800; letter-spacing: 1px; margin-bottom: 25px; text-shadow: 0 0 10px rgba(16,185,129,0.3); }input { width: 100%; padding: 12px; background: #130620; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 18px; box-sizing: border-box; outline:none; font-size:14px; }input:focus { border-color: #10b981; box-shadow: 0 0 12px rgba(16,185,129,0.4); }button { width: 100%; padding: 12px; background: linear-gradient(135deg, #10b981, #059669); border: none; font-weight: bold; cursor: pointer; border-radius: 8px; color: white; font-size: 15px; letter-spacing:1px; transition: 0.3s; }button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(16,185,129,0.4); }.switch-link { color: #a78bfa; font-size: 13px; margin-top: 15px; display: block; text-decoration: none; }</style></head><body><div class="login-card">""" + BIG_COIN_SVG + """<h2>CREATE MEMBER ACCOUNT</h2><form action="/register" method="POST"><input type="text" name="name" placeholder="Full Name" required><input type="password" name="password" placeholder="Set Password" required><input type="text" name="referrer" placeholder="Sponsor UID (Optional)" value="{{ ref_code }}"><button type="submit">JOIN B4U NETWORK</button></form><a href="/" class="switch-link">Already a member? Login</a></div></body></html>"""

USER_DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>MEMBER HUB - B4U NETWORK</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>@keyframes pulse { 0% { transform: scale(0.95); opacity: 0.5; } 100% { transform: scale(1.15); opacity: 0.9; } }body { background: radial-gradient(circle at top, #1c092e 0%, #0c0214 100%); color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 25px; box-sizing: border-box; }h1 { color: #fdb913; padding-bottom: 15px; border-bottom: 2px solid rgba(60, 27, 93, 0.6); font-size: 1.4rem; display: flex; justify-content: space-between; align-items: center; margin-top: 0; }.brand-head { display: flex; align-items: center; gap: 12px; }.brand-title { font-weight: 800; letter-spacing: 1.5px; color: #ffffff; text-shadow: 0 0 15px rgba(253,185,19,0.3); }.trading-hero { background: linear-gradient(135deg, rgba(43, 20, 66, 0.9) 0%, rgba(28, 11, 46, 0.9) 100%); backdrop-filter: blur(10px); border: 1px solid rgba(253, 185, 19, 0.4); border-radius: 18px; padding: 25px 30px; margin-bottom: 25px; box-shadow: 0 10px 35px rgba(253, 185, 19, 0.12); display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 20px; }.hero-left { display: flex; align-items: center; gap: 22px; }.coin-details-title { font-size: 22px; font-weight: 900; color: #ffffff; letter-spacing: 1px; display: flex; align-items: center; gap: 10px; }.pair-badge { background: #fdb913; color: #140620; font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 900; }.sub-tag { font-size: 12px; color: #a78bfa; margin-top: 4px; }.trading-metrics { display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }.metric-box { background: rgba(19, 6, 32, 0.75); border: 1px solid rgba(74, 37, 109, 0.8); border-radius: 12px; padding: 12px 20px; text-align: center; box-shadow: inset 0 0 10px rgba(0,0,0,0.5); }.metric-label { font-size: 10px; color: #a78bfa; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }.metric-val { font-size: 18px; font-weight: bold; color: #ffffff; margin-top: 4px; }.price-display { text-align: right; background: rgba(0,0,0,0.3); padding: 14px 22px; border-radius: 14px; border-right: 4px solid #10b981; border-top: 1px solid rgba(255,255,255,0.05); }.main-price { font-size: 28px; font-weight: 900; color: #fdb913; font-family: 'Courier New', monospace; text-shadow: 0 0 10px rgba(253,185,19,0.4); }.btc-pair { font-size: 13px; color: #f59e0b; font-weight: bold; margin-top: 2px; }.price-change { font-size: 12px; font-weight: bold; padding: 2px 8px; border-radius: 12px; display: inline-block; margin-top: 5px; }.up { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; }.stat-card { background: rgba(35, 13, 56, 0.7); backdrop-filter: blur(8px); border: 1px solid rgba(74, 37, 109, 0.7); border-radius: 14px; padding: 20px; text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.4); transition: 0.3s; }.stat-card:hover { transform: translateY(-3px); border-color: rgba(253,185,19,0.4); }.stat-num { font-size: 22px; font-weight: bold; color: white; margin-top: 6px; }h2 { color: #fdb913; margin-top: 20px; border-bottom: 1px solid rgba(74, 37, 109, 0.6); padding-bottom: 8px; font-size: 15px; font-weight: 700; letter-spacing: 0.5px; }.box { background: rgba(35, 13, 56, 0.75); backdrop-filter: blur(10px); padding: 22px; border-radius: 16px; margin-bottom: 25px; border-top: 4px solid #8b5cf6; border-left: 1px solid rgba(74, 37, 109, 0.7); border-right: 1px solid rgba(74, 37, 109, 0.7); border-bottom: 1px solid rgba(74, 37, 109, 0.7); box-shadow: 0 10px 30px rgba(0,0,0,0.4); }.box.deposit { border-top-color: #10b981; }.box.withdraw { border-top-color: #ef4444; }.box.p2p { border-top-color: #3b82f6; }.box.tree { border-top-color: #fdb913; }.form-inline { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-top: 12px; }input, select { background: rgba(19, 6, 32, 0.85); color: white; border: 1px solid rgba(90, 42, 138, 0.8); padding: 11px 14px; border-radius: 10px; box-sizing: border-box; min-width: 160px; outline: none; font-size: 13px; transition: 0.2s; }input:focus, select:focus { border-color: #fdb913; box-shadow: 0 0 10px rgba(253, 185, 19, 0.3); }.btn { color: white; padding: 11px 20px; border: none; border-radius: 10px; cursor: pointer; font-weight: bold; white-space: nowrap; transition: 0.3s; font-size: 13px; letter-spacing: 0.5px; }.btn:hover { opacity: 0.95; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.5); }.table-wrapper { width: 100%; overflow-x: auto; background: rgba(19, 6, 32, 0.9); margin-top: 12px; border-radius: 12px; border: 1px solid rgba(60, 27, 93, 0.8); }table { width: 100%; border-collapse: collapse; min-width: 600px; }th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid rgba(43, 20, 66, 0.6); font-size: 13px; }th { background-color: rgba(16, 4, 26, 0.95); color: #fdb913; font-weight: 700; }.logout-btn { background: #ef4444; color: white; text-decoration: none; padding: 7px 16px; border-radius: 8px; font-size: 12px; font-weight: bold; transition: 0.2s; }.logout-btn:hover { background: #dc2626; }.ref-box { background: rgba(16, 4, 26, 0.8); border: 1px dashed rgba(253, 185, 19, 0.5); padding: 14px 18px; border-radius: 10px; color: #fdb913; font-family: monospace; font-size: 13px; display: flex; justify-content: space-between; align-items: center; margin-top: 12px; gap: 10px; flex-wrap: wrap; }.copy-btn { background: #fdb913; color: #140620; border: none; padding: 7px 16px; font-weight: bold; border-radius: 8px; cursor: pointer; transition: 0.2s; }.copy-btn:hover { background: #e28700; }.msg-alert { padding: 14px; border-radius: 10px; margin-bottom: 22px; font-size: 14px; font-weight: bold; text-align: center; backdrop-filter: blur(5px); }.msg-success { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); }.msg-error { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); }</style></head><body><h1><div class="brand-head">""" + SMALL_COIN_SVG + """<span class="brand-title">WELCOME, {{ user.name if user else 'MEMBER' }}</span></div><div><span style="font-size: 12px; color: #fdb913; border: 1px solid rgba(253,185,19,0.5); padding: 6px 14px; border-radius: 20px; margin-right: 12px; background: rgba(253,185,19,0.1); font-weight: bold;">NODE: {{ user.uid if user else '' }}</span><a href="/logout" class="logout-btn">LOGOUT</a></div></h1>{% if msg %}<div class="msg-alert msg-{{ msg_type }}">{{ msg }}</div>{% endif %}<div class="trading-hero"><div class="hero-left">""" + BIG_COIN_SVG + """<div><div class="coin-details-title">B4U COIN <span class="pair-badge">B4U / BTC</span></div><div class="sub-tag">⚡ Sovereign Digital Asset • Automated Liquidity Engine</div></div></div><div class="trading-metrics"><div class="metric-box"><div class="metric-label">BITCOIN BENCHMARK</div><div class="metric-val" style="color: #f59e0b;">${{ "{:,.2f}".format(btc_usd) }}</div></div><div class="metric-box"><div class="metric-label">NETWORK LIQUIDITY</div><div class="metric-val">${{ "{:,.2f}".format(total_inv) }}</div></div><div class="metric-box"><div class="metric-label">YOUR HOLDINGS</div><div class="metric-val" style="color: #fdb913;">{{ coin_holdings }} B4U</div></div></div><div class="price-display"><div class="main-price">${{ coin_price }} USD</div><div class="btc-pair">₿ {{ b4u_in_btc }} BTC</div><div class="price-change up">{% if coin_change >= 0 %}+{% endif %}{{ coin_change }}% Growth</div></div></div><div class="stats-grid"><div class="stat-card" style="border-left: 4px solid #fdb913;"><small style="color:#a78bfa; font-weight:bold;">MY RANK</small><div class="stat-num" style="color:#fdb913;">{{ user.rank if user else 'Tiffany' }}</div></div><div class="stat-card" style="border-left: 4px solid #10b981;"><small style="color:#a78bfa; font-weight:bold;">ACTIVE INVESTMENT</small><div class="stat-num">${{ user.inv if user else 0.0 }}</div></div><div class="stat-card" style="border-left: 4px solid #8b5cf6;"><small style="color:#a78bfa; font-weight:bold;">PROFIT WALLET</small><div class="stat-num">${{ user.profit_wallet if user else 0.0 }}</div></div><div class="stat-card" style="border-left: 4px solid #3b82f6;"><small style="color:#a78bfa; font-weight:bold;">P2P WALLET FUNDS</small><div class="stat-num" style="color:#60a5fa;">${{ user.p2p_wallet if user and user.p2p_wallet is not none else 0.0 }}</div></div><div class="stat-card" style="border-left: 4px solid #f59e0b;"><small style="color:#a78bfa; font-weight:bold;">TEAM VOLUME</small><div class="stat-num">${{ team_volume }}</div></div></div><div class="box"><h2>🔗 Your Personal Live Referral Link</h2><p style="font-size: 13px; color: #a78bfa; margin: 4px 0 0 0;">Share your exact live domain link to register downline members directly under you:</p><div class="ref-box"><span id="refUrl">{{ ref_url }}</span><button onclick="copyRefLink()" class="copy-btn">COPY LINK</button></div></div><div class="box p2p"><h2>💸 P2P Wallet Transfer (Member-to-Member)</h2><p style="font-size: 13px; color: #a78bfa; margin: 4px 0 0 0;">Transfer funds instantly from your Profit Wallet to another network member:</p><form action="/p2p_transfer" method="POST" class="form-inline"><input type="text" name="recipient_uid" placeholder="Recipient Node UID (e.g. B4U1003)" required style="flex:1; min-width:220px;"><input type="number" step="0.01" name="amount" placeholder="Amount ($)" required style="width:140px;"><button type="submit" class="btn" style="background: linear-gradient(135deg, #3b82f6, #1d4ed8);">TRANSFER NOW</button></form></div><div class="box tree"><h2>🌳 Downline Network Tree</h2><div class="table-wrapper"><table><thead><tr><th>Level</th><th>Node UID</th><th>Member Name</th><th>Rank</th><th>Active Investment</th><th>Status</th></tr></thead><tbody>{% for member in downline_tree %}<tr><td><b style="color:#fdb913;">L{{ member.level }}</b></td><td><code>{{ member.uid }}</code></td><td>{{ member.name }}</td><td>{{ member.rank }}</td><td><b style="color:#10b981;">${{ member.inv }}</b></td><td><span style="color:#10b981;">{{ member.status }}</span></td></tr>{% else %}<tr><td colspan="6" style="text-align:center; color:#a78bfa;">No downline team members found yet. Share your link to recruit partners!</td></tr>{% endfor %}</tbody></table></div></div><div class="box deposit"><h2>📥 Deposit Capital</h2><form action="/deposit" method="POST" class="form-inline"><select name="method" required><option value="USDT (TRC20)">USDT (TRC20)</option><option value="Bank Transfer">Bank Transfer</option><option value="EasyPaisa/JazzCash">EasyPaisa / JazzCash</option></select><input type="number" step="0.01" name="amount" placeholder="Amount ($)" required style="flex:1; min-width:180px;"><button type="submit" class="btn" style="background: linear-gradient(135deg, #10b981, #059669);">SUBMIT DEPOSIT PROOF</button></form></div><div class="box withdraw"><h2>📤 Withdraw Funds</h2><form action="/withdraw" method="POST" class="form-inline"><select name="method" required><option value="USDT TRC20">USDT TRC20</option><option value="Bank Account">Bank Account</option><option value="JazzCash/EasyPaisa">JazzCash / EasyPaisa</option></select><input type="text" name="address" placeholder="Wallet Address / Acc Number" required style="flex:1; min-width:200px;"><input type="number" step="0.01" name="amount" placeholder="Amount ($)" required style="width:130px;"><button type="submit" class="btn" style="background: linear-gradient(135deg, #ef4444, #dc2626);">REQUEST WITHDRAWAL</button></form></div><div class="box"><h2>📜 Recent Transaction History</h2><div class="table-wrapper"><table><thead><tr><th>Type</th><th>Details / Address</th><th>Amount</th><th>Status / Date</th></tr></thead><tbody>{% for p2p in p2p_history %}<tr><td><span style="color:#3b82f6; font-weight:bold;">P2P TRANSFER</span></td><td>From <code>{{ p2p.sender }}</code> ➔ To <code>{{ p2p.recipient }}</code></td><td><b>${{ p2p.amount }}</b></td><td><i>{{ p2p.created_at }}</i></td></tr>{% endfor %}{% for dep in deposits %}<tr><td><span style="color:#10b981; font-weight:bold;">DEPOSIT</span></td><td>{{ dep.method }}</td><td><b>${{ dep.amount }}</b></td><td><i>{{ dep.status }}</i></td></tr>{% endfor %}{% for wit in withdrawals %}<tr><td><span style="color:#ef4444; font-weight:bold;">WITHDRAWAL</span></td><td><code>{{ wit.method }} - {{ wit.address }}</code></td><td><b>${{ wit.amount }}</b></td><td><i>{{ wit.status }}</i></td></tr>{% endfor %}</tbody></table></div></div><script>function copyRefLink() {var refText = document.getElementById("refUrl").innerText;navigator.clipboard.writeText(refText);alert("Referral Link copied to clipboard!");}</script></body></html>"""

@user_app.route('/')
def user_dashboard():
    ref_code = request.args.get('ref')
    if ref_code and not session.get('user_uid'):
        return redirect(url_for('user_register_page', ref=ref_code))

    if not session.get('user_uid'):
        return render_template_string(USER_LOGIN_HTML, error=None, msg=None)

    uid = session['user_uid']
    msg = session.pop('flash_msg', None)
    msg_type = session.pop('flash_type', 'success')

    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
        deposits = conn.execute("SELECT * FROM deposits WHERE uid = ? ORDER BY id DESC", (uid,)).fetchall()
        withdrawals = conn.execute("SELECT * FROM withdrawals WHERE uid = ? ORDER BY id DESC", (uid,)).fetchall()
        p2p_history = conn.execute("SELECT * FROM p2p_transfers WHERE sender = ? OR recipient = ? ORDER BY id DESC", (uid, uid)).fetchall()

    team_vol = calculate_team_investment(uid)
    downline_tree = get_downline_tree(uid)
    coin_price, coin_change, total_inv, btc_usd, b4u_in_btc = get_coin_price()
    user_inv = float(user['inv'] or 0.0) if user else 0.0
    coin_holdings = round(user_inv / coin_price, 2) if coin_price > 0 else 0.0

    ref_url = f"https://b4u-user-portal.onrender.com/register?ref={uid}"

    return render_template_string(
        USER_DASHBOARD_HTML,
        user=user,
        deposits=deposits,
        withdrawals=withdrawals,
        p2p_history=p2p_history,
        downline_tree=downline_tree,
        team_volume=round(team_vol, 2),
        coin_price=coin_price,
        coin_change=coin_change,
        total_inv=total_inv,
        btc_usd=btc_usd,
        b4u_in_btc=b4u_in_btc,
        coin_holdings=coin_holdings,
        ref_url=ref_url,
        msg=msg,
        msg_type=msg_type
    )

@user_app.route('/register', methods=['GET', 'POST'])
def user_register_page():
    if request.method == 'GET':
        ref_code = request.args.get('ref', '')
        return render_template_string(USER_REGISTER_HTML, ref_code=ref_code)

    name = request.form.get('name')
    password = request.form.get('password')
    referrer = request.form.get('referrer') or None
    new_uid = generate_next_uid()
    hashed_pwd = generate_password_hash(password)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (uid, name, password, rank, inv, profit_wallet, p2p_wallet, status, referrer, created_at) VALUES (?, ?, ?, 'Tiffany', 0.0, 0.0, 0.0, 'Active', ?, ?)",
            (new_uid, name, hashed_pwd, referrer, datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()

    return render_template_string(USER_LOGIN_HTML, error=None, msg=f"Account created successfully! Your Node UID is {new_uid}. Please login.")

@user_app.route('/login', methods=['POST'])
def user_login():
    uid = request.form.get('uid')
    password = request.form.get('password')

    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()

    if user and (check_password_hash(user['password'], password) or user['password'] == password):
        if user['status'] == 'Suspended':
            return render_template_string(USER_LOGIN_HTML, error="Account Suspended! Contact Admin.", msg=None)
        session['user_uid'] = user['uid']
        return redirect('/')

    return render_template_string(USER_LOGIN_HTML, error="Invalid UID or Password!", msg=None)

@user_app.route('/logout')
def user_logout():
    session.clear()
    return redirect('/')

@user_app.route('/p2p_transfer', methods=['POST'])
def user_p2p_transfer():
    if not session.get('user_uid'):
        return redirect('/')

    sender_uid = session['user_uid']
    recipient_uid = request.form.get('recipient_uid', '').strip()
    amount = float(request.form.get('amount') or 0)

    if amount <= 0:
        session['flash_msg'] = "Invalid transfer amount!"
        session['flash_type'] = "error"
        return redirect('/')

    if sender_uid == recipient_uid:
        session['flash_msg'] = "You cannot transfer funds to yourself!"
        session['flash_type'] = "error"
        return redirect('/')

    with get_db() as conn:
        sender = conn.execute("SELECT profit_wallet FROM users WHERE uid = ?", (sender_uid,)).fetchone()
        recipient = conn.execute("SELECT uid FROM users WHERE uid = ?", (recipient_uid,)).fetchone()

        if not recipient:
            session['flash_msg'] = f"Recipient Node {recipient_uid} not found!"
            session['flash_type'] = "error"
            return redirect('/')

        if not sender or float(sender['profit_wallet']) < amount:
            session['flash_msg'] = "Insufficient funds in Profit Wallet!"
            session['flash_type'] = "error"
            return redirect('/')

        conn.execute("UPDATE users SET profit_wallet = round(profit_wallet - ?, 2) WHERE uid = ?", (amount, sender_uid))
        conn.execute("UPDATE users SET p2p_wallet = round(p2p_wallet + ?, 2) WHERE uid = ?", (amount, recipient_uid))
        conn.execute(
            "INSERT INTO p2p_transfers (sender, recipient, amount, created_at) VALUES (?, ?, ?, ?)",
            (sender_uid, recipient_uid, amount, datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()

    session['flash_msg'] = f"Successfully transferred ${amount} to P2P Wallet of {recipient_uid}!"
    session['flash_type'] = "success"
    return redirect('/')

@user_app.route('/deposit', methods=['POST'])
def user_deposit():
    if not session.get('user_uid'):
        return redirect('/')

    uid = session['user_uid']
    method = request.form.get('method')
    amount = float(request.form.get('amount') or 0)

    if amount > 0:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO deposits (uid, amount, method, status, created_at) VALUES (?, ?, ?, '⏳ Pending Verification', ?)",
                (uid, amount, method, datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
        session['flash_msg'] = "Deposit proof submitted successfully!"
        session['flash_type'] = "success"

    return redirect('/')

@user_app.route('/withdraw', methods=['POST'])
def user_withdraw():
    if not session.get('user_uid'):
        return redirect('/')

    uid = session['user_uid']
    method = request.form.get('method')
    address = request.form.get('address')
    amount = float(request.form.get('amount') or 0)

    with get_db() as conn:
        user = conn.execute("SELECT profit_wallet FROM users WHERE uid = ?", (uid,)).fetchone()
        if user and amount > 0 and float(user['profit_wallet']) >= amount:
            conn.execute("UPDATE users SET profit_wallet = round(profit_wallet - ?, 2) WHERE uid = ?", (amount, uid))
            conn.execute(
                "INSERT INTO withdrawals (uid, amount, method, address, status, created_at) VALUES (?, ?, ?, ?, '⏳ Pending Approval', ?)",
                (uid, amount, method, address, datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            session['flash_msg'] = "Withdrawal request submitted!"
            session['flash_type'] = "success"
        else:
            session['flash_msg'] = "Insufficient profit wallet balance for withdrawal!"
            session['flash_type'] = "error"

    return redirect('/')

if __name__ == '__main__':
    user_app.run(host='0.0.0.0', port=50001, debug=False)
