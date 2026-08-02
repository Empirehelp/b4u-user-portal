import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, redirect, render_template_string, session

user_app = Flask('user_app')
user_app.secret_key = os.environ.get('SECRET_KEY', 'b4u_empire_shadow_sovereign_gate_2026')
DB_FILE = "database.db"

# Fixed key quotes syntax error
RANKS_CONFIG = {
    "Tiffany": {"min_p": 10, "max_p": 699, "min_t": 0},
    "Blue Moon": {"min_p": 700, "max_p": 2999, "min_t": 5000},
    "Aurora": {"min_p": 3000, "max_p": 9999, "min_t": 30000},
    "Cullinan": {"min_p": 10000, "max_p": 29999, "min_t": 100000},
    "Sancy": {"min_p": 30000, "max_p": 49999, "min_t": 500000},
    "KohiNoor": {"min_p": 50000, "max_p": 1000000, "min_t": 1000000}
}

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_team_investment(uid):
    total = 0.0
    with get_db() as conn:
        refs = conn.execute("SELECT uid, inv FROM users WHERE referrer = ?", (uid,)).fetchall()
        for ref in refs:
            total += float(ref['inv'] or 0.0)
            total += calculate_team_investment(ref['uid'])
    return total

def get_coin_price():
    with get_db() as conn:
        res = conn.execute("SELECT SUM(inv) as total FROM users").fetchone()
        total_inv = float(res['total'] or 0.0) if res else 0.0
        
    base_price = 1.00
    price_growth = (total_inv / 1000.0) * 0.05
    coin_price = round(base_price + price_growth, 4)
    coin_change = round(((coin_price - base_price) / base_price) * 100, 2)

    # Bitcoin benchmark reference rate
    btc_usd = 68500.0
    b4u_in_btc = f"{coin_price / btc_usd:.8f}"
    
    return coin_price, coin_change, total_inv, btc_usd, b4u_in_btc

COIN_FAVICON = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='%23fdb913'/><circle cx='50' cy='50' r='40' fill='%232b1442'/><text x='50%' y='55%' dominant-baseline='middle' text-anchor='middle' fill='%23fdb913' font-family='sans-serif' font-weight='900' font-size='30'>$</text></svg>"

BIG_COIN_SVG = """<div style="position: relative; display: inline-block;"><div style="position: absolute; width: 100px; height: 100px; background: radial-gradient(circle, rgba(253,185,19,0.4) 0%, rgba(43,20,66,0) 70%); border-radius: 50%; top:-10px; left:-10px; animation: pulse 2s infinite alternate;"></div><svg width="85" height="85" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0px 0px 15px rgba(253, 185, 19, 0.8));"><defs><linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffe259" /><stop offset="100%" stop-color="#ffa751" /></linearGradient><linearGradient id="purpleBg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#3c1b5d" /><stop offset="100%" stop-color="#180729" /></linearGradient></defs><circle cx="50" cy="50" r="48" fill="url(#goldGrad)" stroke="#fff" stroke-width="2"/><circle cx="50" cy="50" r="40" fill="url(#purpleBg)" stroke="#fdb913" stroke-width="2"/><text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle" fill="#fdb913" font-family="'Segoe UI', sans-serif" font-weight="900" font-size="34">$</text><text x="50%" y="73%" dominant-baseline="middle" text-anchor="middle" fill="#ffffff" font-family="'Segoe UI', sans-serif" font-weight="900" font-size="10" letter-spacing="1.5">B4U</text></svg></div>"""

SMALL_COIN_SVG = """<svg width="32" height="32" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="48" fill="#fdb913"/><circle cx="50" cy="50" r="40" fill="#2b1442"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="#fdb913" font-family="sans-serif" font-weight="900" font-size="30">$</text></svg>"""

USER_LOGIN_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MEMBER PORTAL - B4U NETWORK</title>
    <link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml">
    <style>
        body { background: #1a0928; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .login-card { background: #2b1442; border-top: 5px solid #fdb913; padding: 40px 35px; border-radius: 16px; width: 340px; box-shadow: 0 15px 35px rgba(0,0,0,0.6); text-align: center; }
        h2 { color: #fdb913; font-size: 20px; margin-top: 15px; font-weight: 800; letter-spacing: 1px; margin-bottom: 25px; }
        input { width: 100%; padding: 12px; background: #130620; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 18px; box-sizing: border-box; outline:none; font-size:14px; }
        input:focus { border-color: #fdb913; box-shadow: 0 0 8px rgba(253, 185, 19, 0.3); }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #fdb913, #e28700); border: none; font-weight: bold; cursor: pointer; border-radius: 8px; color: #1a0928; font-size: 15px; letter-spacing:1px; transition: 0.3s; }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(253, 185, 19, 0.4); }
        .err { color: #ff4d4d; font-size: 13px; margin-bottom: 15px; background: rgba(255,77,77,0.1); padding: 8px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="login-card">
        """ + BIG_COIN_SVG + """
        <h2>B4U MEMBER PORTAL</h2>
        {% if error %}<div class="err">{{ error }}</div>{% endif %}
        <form action="/login" method="POST">
            <input type="text" name="uid" placeholder="Node UID (e.g. B4U1001)" required>
            <input type="password" name="password" placeholder="Access Key" required>
            <button type="submit">LOGIN TO NETWORK</button>
        </form>
    </div>
</body>
</html>"""

USER_DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MEMBER HUB - B4U NETWORK</title>
    <link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml">
    <style>
        @keyframes pulse { 0% { transform: scale(0.95); opacity: 0.5; } 100% { transform: scale(1.15); opacity: 0.9; } }
        body { background-color: #140620; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; box-sizing: border-box; }
        h1 { color: #fdb913; padding-bottom: 12px; border-bottom: 2px solid #3c1b5d; font-size: 1.4rem; display: flex; justify-content: space-between; align-items: center; margin-top: 0; }
        .brand-head { display: flex; align-items: center; gap: 12px; }
        .brand-title { font-weight: 800; letter-spacing: 1.5px; color: #ffffff; }
        .trading-hero { background: linear-gradient(135deg, #2b1442 0%, #1c0b2e 100%); border: 2px solid #fdb913; border-radius: 16px; padding: 22px 28px; margin-bottom: 25px; box-shadow: 0 8px 30px rgba(253, 185, 19, 0.15); display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 20px; }
        .hero-left { display: flex; align-items: center; gap: 22px; }
        .coin-details-title { font-size: 22px; font-weight: 900; color: #ffffff; letter-spacing: 1px; display: flex; align-items: center; gap: 10px; }
        .pair-badge { background: #fdb913; color: #140620; font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 900; }
        .sub-tag { font-size: 12px; color: #a78bfa; margin-top: 4px; }
        .trading-metrics { display: flex; gap: 25px; align-items: center; flex-wrap: wrap; }
        .metric-box { background: rgba(19, 6, 32, 0.7); border: 1px solid #4a256d; border-radius: 10px; padding: 10px 18px; text-align: center; }
        .metric-label { font-size: 10px; color: #a78bfa; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-val { font-size: 18px; font-weight: bold; color: #ffffff; margin-top: 3px; }
        .price-display { text-align: right; background: rgba(0,0,0,0.2); padding: 12px 20px; border-radius: 12px; border-right: 4px solid #10b981; }
        .main-price { font-size: 30px; font-weight: 900; color: #fdb913; font-family: 'Courier New', monospace; }
        .btc-pair { font-size: 13px; color: #f59e0b; font-weight: bold; margin-top: 2px; }
        .price-change { font-size: 12px; font-weight: bold; padding: 2px 8px; border-radius: 12px; display: inline-block; margin-top: 5px; }
        .up { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; }
        .stat-card { background: #2b1442; border: 1px solid #4a256d; border-radius: 10px; padding: 18px; text-align: center; }
        .stat-num { font-size: 22px; font-weight: bold; color: white; margin-top: 5px; }
        h2 { color: #fdb913; margin-top: 20px; border-bottom: 1px solid #4a256d; padding-bottom: 8px; font-size: 15px; font-weight: 700; }
        .box { background: #2b1442; padding: 20px; border-radius: 12px; margin-bottom: 25px; border-top: 4px solid #8b5cf6; border-left: 1px solid #4a256d; border-right: 1px solid #4a256d; border-bottom: 1px solid #4a256d; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        .box.deposit { border-top-color: #10b981; }
        .box.withdraw { border-top-color: #ef4444; }
        .form-inline { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
        input, select { background: #140620; color: white; border: 1px solid #5a2a8a; padding: 10px; border-radius: 8px; box-sizing: border-box; min-width: 140px; outline: none; font-size: 13px; }
        input:focus, select:focus { border-color: #fdb913; }
        .btn { background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 10px 18px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; white-space: nowrap; transition: 0.2s; }
        .btn:hover { opacity: 0.9; transform: translateY(-1px); }
        .table-wrapper { width: 100%; overflow-x: auto; background: #140620; margin-top: 10px; border-radius: 10px; border: 1px solid #3c1b5d; }
        table { width: 100%; border-collapse: collapse; min-width: 600px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #2b1442; font-size: 13px; }
        th { background-color: #10041a; color: #fdb913; font-weight: 700; }
        .logout-btn { background: #ef4444; color: white; text-decoration: none; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: bold; }
        .ref-box { background: #10041a; border: 1px dashed #fdb913; padding: 10px; border-radius: 8px; color: #fdb913; font-family: monospace; font-size: 14px; text-align: center; margin-top: 10px; word-break: break-all; }
    </style>
</head>
<body>
    <h1>
        <div class="brand-head">
            """ + SMALL_COIN_SVG + """
            <span class="brand-title">WELCOME, {{ user.name }}</span>
        </div>
        <div>
            <span style="font-size: 12px; color: #fdb913; border: 1px solid #fdb913; padding: 4px 12px; border-radius: 20px; margin-right: 10px; background: rgba(253,185,19,0.1);">NODE: {{ user.uid }}</span>
            <a href="/logout" class="logout-btn">LOGOUT</a>
        </div>
    </h1>

    <div class="trading-hero">
        <div class="hero-left">
            """ + BIG_COIN_SVG + """
            <div>
                <div class="coin-details-title">B4U COIN <span class="pair-badge">B4U / BTC</span></div>
                <div class="sub-tag">⚡ Sovereign Digital Asset • Automated Liquidity Engine</div>
            </div>
        </div>
        <div class="trading-metrics">
            <div class="metric-box">
                <div class="metric-label">BITCOIN BENCHMARK</div>
                <div class="metric-val" style="color: #f59e0b;">${{ "{:,.2f}".format(btc_usd) }}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">NETWORK LIQUIDITY</div>
                <div class="metric-val">${{ "{:,.2f}".format(total_inv) }}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">YOUR HOLDINGS</div>
                <div class="metric-val" style="color: #fdb913;">{{ coin_holdings }} B4U</div>
            </div>
        </div>
        <div class="price-display">
            <div class="main-price">${{ coin_price }} USD</div>
            <div class="btc-pair">₿ {{ b4u_in_btc }} BTC</div>
            <div class="price-change up">{% if coin_change >= 0 %}+{% endif %}{{ coin_change }}% Growth</div>
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card" style="border-left: 4px solid #fdb913;">
            <small style="color:#a78bfa;">MY RANK</small>
            <div class="stat-num" style="color:#fdb913;">{{ user.rank }}</div>
        </div>
        <div class="stat-card" style="border-left: 4px solid #10b981;">
            <small style="color:#a78bfa;">TOTAL ACTIVE INVESTMENT</small>
            <div class="stat-num">${{ user.inv }}</div>
        </div>
        <div class="stat-card" style="border-left: 4px solid #8b5cf6;">
            <small style="color:#a78bfa;">PROFIT WALLET</small>
            <div class="stat-num">${{ user.profit_wallet }}</div>
        </div>
        <div class="stat-card" style="border-left: 4px solid #3b82f6;">
            <small style="color:#a78bfa;">TEAM VOLUME</small>
            <div class="stat-num">${{ team_volume }}</div>
        </div>
    </div>

    <div class="box">
        <h2>🔗 Your Referral Connection Key</h2>
        <p style="font-size: 13px; color: #a78bfa; margin: 0;">Share your UID with new partners to build your downline team:</p>
        <div class="ref-box">REFERRAL CODE: <b>{{ user.uid }}</b></div>
    </div>

    <div class="box deposit">
        <h2>📥 Deposit Capital</h2>
        <form action="/deposit" method="POST" class="form-inline">
            <select name="method" required>
                <option value="USDT (TRC20)">USDT (TRC20)</option>
                <option value="Bank Transfer">Bank Transfer</option>
                <option value="EasyPaisa/JazzCash">EasyPaisa / JazzCash</option>
            </select>
            <input type="number" step="0.01" name="amount" placeholder="Amount ($)" required>
            <button type="submit" class="btn" style="background: linear-gradient(135deg, #10b981, #059669);">SUBMIT DEPOSIT PROOF</button>
        </form>
    </div>

    <div class="box withdraw">
        <h2>📤 Withdraw Funds</h2>
        <form action="/withdraw" method="POST" class="form-inline">
            <select name="method" required>
                <option value="USDT TRC20">USDT TRC20</option>
                <option value="Bank Account">Bank Account</option>
                <option value="JazzCash/EasyPaisa">JazzCash / EasyPaisa</option>
            </select>
            <input type="text" name="address" placeholder="Wallet Address / Acc Number" required style="width:220px;">
            <input type="number" step="0.01" name="amount" placeholder="Amount ($)" required>
            <button type="submit" class="btn" style="background: linear-gradient(135deg, #ef4444, #dc2626);">REQUEST WITHDRAWAL</button>
        </form>
    </div>

    <div class="box">
        <h2>📜 Recent Transaction History</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Method / Address</th>
                        <th>Amount</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for dep in deposits %}
                    <tr>
                        <td><span style="color:#10b981; font-weight:bold;">DEPOSIT</span></td>
                        <td>{{ dep.method }}</td>
                        <td><b>${{ dep.amount }}</b></td>
                        <td><i>{{ dep.status }}</i></td>
                    </tr>
                    {% endfor %}
                    {% for wit in withdrawals %}
                    <tr>
                        <td><span style="color:#ef4444; font-weight:bold;">WITHDRAWAL</span></td>
                        <td><code>{{ wit.method }} - {{ wit.address }}</code></td>
                        <td><b>${{ wit.amount }}</b></td>
                        <td><i>{{ wit.status }}</i></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""

@user_app.route('/')
def user_dashboard():
    if not session.get('user_uid'):
        return render_template_string(USER_LOGIN_HTML, error=None)
    
    uid = session['user_uid']
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
        deposits = conn.execute("SELECT * FROM deposits WHERE uid = ? ORDER BY id DESC", (uid,)).fetchall()
        withdrawals = conn.execute("SELECT * FROM withdrawals WHERE uid = ? ORDER BY id DESC", (uid,)).fetchall()
        
    team_vol = calculate_team_investment(uid)
    coin_price, coin_change, total_inv, btc_usd, b4u_in_btc = get_coin_price()
    
    user_inv = float(user['inv'] or 0.0)
    coin_holdings = round(user_inv / coin_price, 2) if coin_price > 0 else 0.0
    
    return render_template_string(
        USER_DASHBOARD_HTML,
        user=user,
        deposits=deposits,
        withdrawals=withdrawals,
        team_volume=round(team_vol, 2),
        coin_price=coin_price,
        coin_change=coin_change,
        total_inv=total_inv,
        btc_usd=btc_usd,
        b4u_in_btc=b4u_in_btc,
        coin_holdings=coin_holdings
    )

@user_app.route('/login', methods=['POST'])
def user_login():
    uid = request.form.get('uid')
    password = request.form.get('password')
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
        if user and check_password_hash(user['password'], password):
            if user['status'] == 'Suspended':
                return render_template_string(USER_LOGIN_HTML, error="Account Suspended! Contact Admin.")
            session['user_uid'] = user['uid']
            return redirect('/')
    return render_template_string(USER_LOGIN_HTML, error="Invalid UID or Password!")

@user_app.route('/logout')
def user_logout():
    session.clear()
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
                "INSERT INTO deposits (uid, amount, method, status) VALUES (?, ?, ?, '⏳ Pending Verification')",
                (uid, amount, method)
            )
            conn.commit()
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
                "INSERT INTO withdrawals (uid, amount, method, address, status) VALUES (?, ?, ?, ?, '⏳ Pending Approval')",
                (uid, amount, method, address)
            )
            conn.commit()
    return redirect('/')

if __name__ == '__main__':
    user_app.run(host='0.0.0.0', port=50001, debug=False)
