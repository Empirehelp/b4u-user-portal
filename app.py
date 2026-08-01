import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect, render_template_string, session, send_from_directory

user_app = Flask('user_app')
user_app.secret_key = os.environ.get('SECRET_KEY', 'b4u_empire_shadow_sovereign_gate_2026')

DB_FILE = "database.db"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
user_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

RANKS_CONFIG = {
    "Tiffany": {"min_p": 10, "max_p": 699, "min_t": 0},
    "Blue Moon": {"min_p": 700, "max_p": 2999, "min_t": 5000},
    "Aurora": {"min_p": 3000, "max_p": 9999, "min_t": 30000},
    "Cullinan": {"min_p": 10000, "max_p": 29999, "min_t": 100000},
    "Sancy": {"min_p": 30000, "max_p": 49999, "min_t": 500000},
    "KohiNoor": {"min_p": 50000, "max_p": 1000000, "min_t": 1000000}
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

with get_db() as conn:
    try:
        conn.execute("ALTER TABLE deposits ADD COLUMN proof_file TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

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
    base_price = 3.14
    price_growth = (total_inv / 1000.0) * 0.05
    coin_price = round(base_price + price_growth, 4)
    coin_change = round(4.85, 2)
    btc_usd = 68500.0
    b4u_in_btc = f"{coin_price / btc_usd:.8f}"
    return coin_price, coin_change, total_inv, btc_usd, b4u_in_btc

COIN_FAVICON = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='%23111019'/><circle cx='50' cy='50' r='42' fill='none' stroke='%23f0b90b' stroke-width='4'/><text x='50%' y='56%' dominant-baseline='middle' text-anchor='middle' fill='%23f0b90b' font-family='sans-serif' font-weight='900' font-size='42'>π</text></svg>"

BIG_COIN_SVG = """<div style="position: relative; display: inline-block;"><div style="position: absolute; width: 110px; height: 110px; background: radial-gradient(circle, rgba(240,185,11,0.3) 0%, rgba(17,16,25,0) 75%); border-radius: 50%; top:-12px; left:-12px; animation: pulse 2.5s infinite alternate;"></div><svg width="88" height="88" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0px 0px 20px rgba(240, 185, 11, 0.6));"><defs><linearGradient id="piGold" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#f8d347" /><stop offset="100%" stop-color="#d49b08" /></linearGradient><linearGradient id="piDark" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#1c1a29" /><stop offset="100%" stop-color="#0b0a12" /></linearGradient></defs><circle cx="50" cy="50" r="48" fill="url(#piGold)"/><circle cx="50" cy="50" r="43" fill="url(#piDark)"/><text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle" fill="#f0b90b" font-family="'Segoe UI', sans-serif" font-weight="900" font-size="52" style="text-shadow: 0 2px 10px rgba(240,185,11,0.5);">π</text></svg></div>"""

SMALL_COIN_SVG = """<svg width="36" height="36" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="48" fill="#f0b90b"/><circle cx="50" cy="50" r="42" fill="#111019"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="#f0b90b" font-family="sans-serif" font-weight="900" font-size="44">π</text></svg>"""

USER_LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>PI ECOSYSTEM - SECURE PORTAL</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>body { background: #0b0a12; color: #f0f0f5; font-family: 'Inter', 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }.login-card { background: linear-gradient(145deg, #161424, #0f0e1a); border: 1px solid rgba(240, 185, 11, 0.3); padding: 45px 35px; border-radius: 24px; width: 360px; box-shadow: 0 25px 50px rgba(0,0,0,0.9), 0 0 30px rgba(240,185,11,0.1); text-align: center; }h2 { color: #f0b90b; font-size: 20px; margin-top: 20px; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 30px; }input { width: 100%; padding: 14px 16px; background: #07060b; border: 1px solid #2a2640; border-radius: 12px; color: white; margin-bottom: 18px; box-sizing: border-box; outline: none; font-size: 14px; transition: 0.3s; }input:focus { border-color: #f0b90b; box-shadow: 0 0 12px rgba(240, 185, 11, 0.3); }button { width: 100%; padding: 14px; background: linear-gradient(135deg, #f0b90b, #c69305); border: none; font-weight: 800; cursor: pointer; border-radius: 12px; color: #0b0a12; font-size: 15px; letter-spacing: 1px; transition: 0.3s; box-shadow: 0 4px 15px rgba(240,185,11,0.3); }button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(240, 185, 11, 0.5); }.err { color: #ff5252; font-size: 13px; margin-bottom: 20px; background: rgba(255,82,82,0.1); border: 1px solid rgba(255,82,82,0.3); padding: 12px; border-radius: 10px; }</style></head><body><div class="login-card">""" + BIG_COIN_SVG + """<h2>PI NETWORK AUTH</h2>{% if error %}<div class="err">{{ error }}</div>{% endif %}<form action="/login" method="POST"><input type="text" name="uid" placeholder="Node UID (e.g. B4U1001)" required><input type="password" name="password" placeholder="Passcode / Access Key" required><button type="submit">UNLOCK MAINNET PORTAL</button></form></div></body></html>"""

USER_DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>PI ECOSYSTEM - MAINNET TERMINAL</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>@keyframes pulse { 0% { transform: scale(0.95); opacity: 0.5; } 100% { transform: scale(1.15); opacity: 0.9; } }body { background-color: #0b0a12; color: #f0f0f5; font-family: 'Inter', 'Segoe UI', sans-serif; margin: 0; padding: 25px; box-sizing: border-box; }h1 { color: #f0b90b; padding-bottom: 18px; border-bottom: 1px solid rgba(240,185,11,0.2); font-size: 1.3rem; display: flex; justify-content: space-between; align-items: center; margin-top: 0; }.brand-head { display: flex; align-items: center; gap: 14px; }.brand-title { font-weight: 800; letter-spacing: 1px; color: #ffffff; font-size: 1.25rem; }.trading-hero { background: linear-gradient(135deg, #161424 0%, #0d0c17 100%); border: 1px solid rgba(240, 185, 11, 0.4); border-radius: 20px; padding: 24px 30px; margin-bottom: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.1); display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 20px; }.hero-left { display: flex; align-items: center; gap: 22px; }.coin-details-title { font-size: 24px; font-weight: 900; color: #ffffff; letter-spacing: 0.5px; display: flex; align-items: center; gap: 10px; }.pair-badge { background: rgba(240, 185, 11, 0.15); color: #f0b90b; border: 1px solid rgba(240, 185, 11, 0.4); font-size: 11px; padding: 3px 10px; border-radius: 6px; font-weight: 800; }.sub-tag { font-size: 12px; color: #9d99b9; margin-top: 5px; font-weight: 500; }.trading-metrics { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }.metric-box { background: rgba(7, 6, 11, 0.7); border: 1px solid #231f36; border-radius: 12px; padding: 12px 20px; text-align: center; }.metric-label { font-size: 10px; color: #9d99b9; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }.metric-val { font-size: 17px; font-weight: 800; color: #ffffff; margin-top: 4px; }.price-display { text-align: right; background: rgba(7,6,11,0.6); padding: 14px 22px; border-radius: 14px; border-left: 3px solid #10b981; border-right: 1px solid #231f36; border-top: 1px solid #231f36; border-bottom: 1px solid #231f36; }.main-price { font-size: 28px; font-weight: 900; color: #f0b90b; font-family: 'Courier New', monospace; }.btc-pair { font-size: 12px; color: #9d99b9; font-weight: 700; margin-top: 2px; }.price-change { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px; display: inline-block; margin-top: 6px; }.up { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); }.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 18px; margin-bottom: 25px; }.stat-card { background: #12101c; border: 1px solid #231f36; border-radius: 16px; padding: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.4); transition: 0.3s; }.stat-card:hover { border-color: rgba(240,185,11,0.4); transform: translateY(-2px); }.stat-num { font-size: 22px; font-weight: 800; color: white; margin-top: 8px; }h2 { color: #f0b90b; margin-top: 0; border-bottom: 1px solid rgba(240,185,11,0.15); padding-bottom: 10px; font-size: 15px; font-weight: 700; display: flex; align-items: center; gap: 10px; letter-spacing: 0.5px; }.box { background: #12101c; padding: 24px; border-radius: 18px; margin-bottom: 25px; border: 1px solid #231f36; box-shadow: 0 8px 25px rgba(0,0,0,0.5); }.box.deposit { border-top: 3px solid #10b981; }.box.withdraw { border-top: 3px solid #ef4444; }.box.p2p { border-top: 3px solid #3b82f6; }.form-inline { display: flex; flex-wrap: wrap; gap: 14px; align-items: center; margin-top: 18px; }input, select { background: #07060b; color: white; border: 1px solid #2a2640; padding: 12px 16px; border-radius: 10px; box-sizing: border-box; min-width: 160px; outline: none; font-size: 13px; transition: 0.2s; }input:focus, select:focus { border-color: #f0b90b; box-shadow: 0 0 10px rgba(240, 185, 11, 0.3); }.file-btn { background: #161424; border: 1px dashed rgba(240,185,11,0.5); color: #f0b90b; padding: 10px 14px; border-radius: 10px; cursor: pointer; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; transition: 0.2s; }.file-btn:hover { background: rgba(240,185,11,0.05); }.btn { background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 12px 22px; border: none; border-radius: 10px; cursor: pointer; font-weight: 700; white-space: nowrap; transition: 0.2s; letter-spacing: 0.5px; font-size: 13px; box-shadow: 0 4px 12px rgba(16,185,129,0.3); }.btn:hover { transform: translateY(-1px); opacity: 0.95; }.table-wrapper { width: 100%; overflow-x: auto; background: #07060b; margin-top: 15px; border-radius: 12px; border: 1px solid #231f36; }table { width: 100%; border-collapse: collapse; min-width: 600px; }th, td { padding: 14px 18px; text-align: left; border-bottom: 1px solid #12101c; font-size: 13px; }th { background-color: #0d0c17; color: #f0b90b; font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 1px; }.logout-btn { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); text-decoration: none; padding: 7px 16px; border-radius: 8px; font-size: 12px; font-weight: 700; transition: 0.2s; }.logout-btn:hover { background: #ef4444; color: white; }.ref-box { background: #07060b; border: 1px dashed rgba(240,185,11,0.4); padding: 14px; border-radius: 10px; color: #f0b90b; font-family: monospace; font-size: 14px; text-align: center; margin-top: 12px; letter-spacing: 1px; }.msg-alert { background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; color: #10b981; padding: 14px; border-radius: 12px; margin-bottom: 22px; font-size: 13px; font-weight: 700; display: flex; align-items: center; gap: 8px; }.err-alert { background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; color: #ef4444; padding: 14px; border-radius: 12px; margin-bottom: 22px; font-size: 13px; font-weight: 700; display: flex; align-items: center; gap: 8px; }</style></head><body><h1><div class="brand-head">""" + SMALL_COIN_SVG + """<span class="brand-title">PI MAINNET PORTAL, {{ user.name|upper }}</span></div><div><span style="font-size: 12px; color: #f0b90b; border: 1px solid rgba(240,185,11,0.4); padding: 6px 14px; border-radius: 20px; margin-right: 12px; background: rgba(240,185,11,0.08); font-weight:700;">NODE: {{ user.uid }}</span><a href="/logout" class="logout-btn">DISCONNECT</a></div></h1>{% if msg %}<div class="msg-alert">✅ {{ msg }}</div>{% endif %}{% if err %}<div class="err-alert">⚠️ {{ err }}</div>{% endif %}<!-- LIVE ASSET & MARKET DASHBOARD --><div class="trading-hero"><div class="hero-left">""" + BIG_COIN_SVG + """<div><div class="coin-details-title">Pi Ecosystem <span class="pair-badge">PI / USDT</span></div><div class="sub-tag">⚡ Decentralized Mainnet • Automated Liquidity Engine</div></div></div><div class="trading-metrics"><div class="metric-box"><div class="metric-label">BITCOIN BENCHMARK</div><div class="metric-val" style="color: #f0b90b;">${{ "{:,.2f}".format(btc_usd) }}</div></div><div class="metric-box"><div class="metric-label">NETWORK LIQUIDITY</div><div class="metric-val">${{ "{:,.2f}".format(total_inv) }}</div></div><div class="metric-box"><div class="metric-label">YOUR HOLDINGS</div><div class="metric-val" style="color: #f0b90b;">{{ coin_holdings }} π</div></div></div><div class="price-display"><div class="main-price">${{ coin_price }} USD</div><div class="btc-pair">₿ {{ b4u_in_btc }} BTC</div><div class="price-change up">{% if coin_change >= 0 %}+{% endif %}{{ coin_change }}% Mainnet Growth</div></div></div><div class="stats-grid"><div class="stat-card" style="border-left: 4px solid #f0b90b;"><small style="color:#9d99b9; font-weight:700;">MAINNET RANK</small><div class="stat-num" style="color:#f0b90b;">{{ user.rank }}</div></div><div class="stat-card" style="border-left: 4px solid #10b981;"><small style="color:#9d99b9; font-weight:700;">TOTAL ACTIVE STAKE</small><div class="stat-num">${{ user.inv }}</div></div><div class="stat-card" style="border-left: 4px solid #8b5cf6;"><small style="color:#9d99b9; font-weight:700;">REWARD WALLET</small><div class="stat-num">${{ user.profit_wallet }}</div></div><div class="stat-card" style="border-left: 4px solid #3b82f6;"><small style="color:#9d99b9; font-weight:700;">TEAM VOLUME</small><div class="stat-num">${{ team_volume }}</div></div></div><div class="box"><h2>🔗 Your Pi Referral Invitation Key</h2><p style="font-size: 13px; color: #9d99b9; margin: 0;">Share your Node UID with new pioneers to expand your security circle:</p><div class="ref-box">PIONEER INVITATION CODE: <b>{{ user.uid }}</b></div></div><!-- DEPOSIT CAPITAL WITH PROOF UPLOAD --><div class="box deposit"><h2>📥 Stake & Deposit Capital with Proof</h2><form action="/deposit" method="POST" enctype="multipart/form-data" class="form-inline"><select name="method" required><option value="USDT (TRC20)">USDT (TRC20)</option><option value="Bank Transfer">Bank Transfer</option><option value="EasyPaisa/JazzCash">EasyPaisa / JazzCash</option></select><input type="number" step="0.01" name="amount" placeholder="Deposit Amount ($)" required><label class="file-btn">📸 Upload Proof Slip<input type="file" name="proof" accept="image/*,.pdf" style="display:none;" onchange="this.parentElement.style.borderColor='#10b981';"></label><button type="submit" class="btn" style="background: linear-gradient(135deg, #10b981, #059669);">SUBMIT PROOF</button></form></div><!-- INSTANT P2P TRANSFER SYSTEM --><div class="box p2p"><h2>🔄 P2P Instant Network Transfer</h2><p style="font-size: 12px; color: #9d99b9; margin: 0;">Transfer funds directly from your Reward Wallet to another Node UID instantly with zero gas fee.</p><form action="/p2p_transfer" method="POST" class="form-inline"><input type="text" name="receiver_uid" placeholder="Recipient Node UID (e.g. B4U1002)" required><input type="number" step="0.01" name="amount" placeholder="Transfer Amount ($)" required><button type="submit" class="btn" style="background: linear-gradient(135deg, #3b82f6, #2563eb);">SEND P2P FUNDS</button></form></div><!-- WITHDRAW FUNDS --><div class="box withdraw"><h2>📤 Request Mainnet Withdrawal</h2><form action="/withdraw" method="POST" class="form-inline"><select name="method" required><option value="USDT TRC20">USDT TRC20</option><option value="Bank Account">Bank Account</option><option value="JazzCash/EasyPaisa">JazzCash / EasyPaisa</option></select><input type="text" name="address" placeholder="Wallet Address / Account No." required style="width:230px;"><input type="number" step="0.01" name="amount" placeholder="Amount ($)" required><button type="submit" class="btn" style="background: linear-gradient(135deg, #ef4444, #dc2626);">REQUEST WITHDRAWAL</button></form></div><!-- TRANSACTION HISTORY TABLE --><div class="box"><h2>📜 Mainnet Ledger & Transactions</h2><div class="table-wrapper"><table><thead><tr><th>Type</th><th>Details / Recipient</th><th>Amount</th><th>Proof Slip</th><th>Status</th></tr></thead><tbody>{% for dep in deposits %}<tr><td><span style="color:#10b981; font-weight:bold;">DEPOSIT</span></td><td>{{ dep.method }}</td><td><b>${{ dep.amount }}</b></td><td>{% if dep.proof_file %}<a href="/uploads/{{ dep.proof_file }}" target="_blank" style="color:#f0b90b; font-weight:bold;">View Proof</a>{% else %}<span style="color:#666;">No File</span>{% endif %}</td><td><i>{{ dep.status }}</i></td></tr>{% endfor %}{% for wit in withdrawals %}<tr><td><span style="color:#ef4444; font-weight:bold;">WITHDRAWAL</span></td><td><code>{{ wit.method }} - {{ wit.address }}</code></td><td><b>${{ wit.amount }}</b></td><td>—</td><td><i>{{ wit.status }}</i></td></tr>{% endfor %}</tbody></table></div></div></body></html>"""

@user_app.route('/')
def user_dashboard():
    if not session.get('user_uid'):
        return render_template_string(USER_LOGIN_HTML, error=None)
    uid = session['user_uid']
    msg = request.args.get('msg')
    err = request.args.get('err')
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
        deposits = conn.execute("SELECT * FROM deposits WHERE uid = ? ORDER BY id DESC", (uid,)).fetchall()
        withdrawals = conn.execute("SELECT * FROM withdrawals WHERE uid = ? ORDER BY id DESC", (uid,)).fetchall()
    team_vol = calculate_team_investment(uid)
    coin_price, coin_change, total_inv, btc_usd, b4u_in_btc = get_coin_price()
    user_inv = float(user['inv'] or 0.0) if user else 0.0
    coin_holdings = round(user_inv / coin_price, 2) if coin_price > 0 else 0.0
    return render_template_string(USER_DASHBOARD_HTML, user=user, deposits=deposits, withdrawals=withdrawals, team_volume=round(team_vol, 2), coin_price=coin_price, coin_change=coin_change, total_inv=total_inv, btc_usd=btc_usd, b4u_in_btc=b4u_in_btc, coin_holdings=coin_holdings, msg=msg, err=err)

@user_app.route('/login', methods=['POST'])
def user_login():
    uid = request.form.get('uid')
    password = request.form.get('password')
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
        if user and check_password_hash(user['password'], password):
            if user['status'] == 'Suspended':
                return render_template_string(USER_LOGIN_HTML, error="Node Suspended! Contact Network Admin.")
            session['user_uid'] = user['uid']
            return redirect('/')
    return render_template_string(USER_LOGIN_HTML, error="Invalid Node UID or Access Passcode!")

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
    filename = None
    if 'proof' in request.files:
        file = request.files['proof']
        if file and allowed_file(file.filename):
            s_filename = secure_filename(file.filename)
            filename = f"{uid}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{s_filename}"
            file.save(os.path.join(user_app.config['UPLOAD_FOLDER'], filename))
    if amount > 0:
        with get_db() as conn:
            conn.execute("INSERT INTO deposits (uid, amount, method, status, proof_file) VALUES (?, ?, ?, '⏳ Pending Verification', ?)", (uid, amount, method, filename))
            conn.commit()
        return redirect('/?msg=Deposit request & proof uploaded successfully!')
    return redirect('/?err=Invalid deposit amount!')

@user_app.route('/p2p_transfer', methods=['POST'])
def p2p_transfer():
    if not session.get('user_uid'): 
        return redirect('/')
    sender_uid = session['user_uid']
    receiver_uid = request.form.get('receiver_uid', '').strip()
    amount = float(request.form.get('amount') or 0)
    if sender_uid == receiver_uid:
        return redirect('/?err=You cannot transfer funds to yourself!')
    if amount <= 0:
        return redirect('/?err=Please enter a valid transfer amount!')
    with get_db() as conn:
        sender = conn.execute("SELECT profit_wallet FROM users WHERE uid = ?", (sender_uid,)).fetchone()
        receiver = conn.execute("SELECT uid, status FROM users WHERE uid = ?", (receiver_uid,)).fetchone()
        if not receiver:
            return redirect('/?err=Recipient Node UID not found!')
        if receiver['status'] == 'Suspended':
            return redirect('/?err=Recipient node is suspended!')
        if sender and float(sender['profit_wallet']) >= amount:
            conn.execute("UPDATE users SET profit_wallet = round(profit_wallet - ?, 2) WHERE uid = ?", (amount, sender_uid))
            conn.execute("UPDATE users SET profit_wallet = round(profit_wallet + ?, 2) WHERE uid = ?", (amount, receiver_uid))
            conn.execute("INSERT INTO withdrawals (uid, amount, method, address, status) VALUES (?, ?, 'P2P Sent', ?, '✅ Instant Completed')", (sender_uid, amount, f"To Node: {receiver_uid}"))
            conn.execute("INSERT INTO deposits (uid, amount, method, status) VALUES (?, ?, 'P2P Received', '✅ Instant Completed')", (receiver_uid, amount))
            conn.commit()
            return redirect(f'/?msg=Successfully transferred ${amount} to {receiver_uid}!')
        else:
            return redirect('/?err=Insufficient balance in your Reward Wallet!')

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
            conn.execute("INSERT INTO withdrawals (uid, amount, method, address, status) VALUES (?, ?, ?, ?, '⏳ Pending Approval')", (uid, amount, method, address))
            conn.commit()
            return redirect('/?msg=Withdrawal request submitted successfully!')
    return redirect('/?err=Insufficient balance or invalid amount!')

@user_app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(user_app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    user_app.run(host='0.0.0.0', port=50001, debug=False)
