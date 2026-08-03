import os
import sqlite3
import random
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect, render_template_string, session, send_from_directory

user_app = Flask('user_app')
app = user_app  # Gunicorn compatibility
app.secret_key = os.environ.get('SECRET_KEY', 'b4u_empire_user_sovereign_gate_2026')

# Use /tmp directory for Render writable SQLite DB
DB_FILE = "/tmp/database.db"
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SIGNUP_BONUS = 100.0

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

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT UNIQUE,
                name TEXT,
                email TEXT UNIQUE,
                password TEXT,
                referrer TEXT,
                inv REAL DEFAULT 0.0,
                profit_wallet REAL DEFAULT 0.0,
                rank TEXT DEFAULT 'Tiffany',
                status TEXT DEFAULT 'Active',
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT,
                amount REAL,
                method TEXT,
                proof_file TEXT,
                status TEXT DEFAULT '⏳ Pending',
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT,
                amount REAL,
                method TEXT,
                address TEXT,
                status TEXT DEFAULT '⏳ Pending',
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS p2p_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_uid TEXT,
                receiver_uid TEXT,
                amount REAL,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('announcement', '🚀 Welcome to B4U Sovereign Empire!')")
        conn.commit()

@app.before_request
def setup_db_before_request():
    init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_user_rank(conn, uid):
    user = conn.execute("SELECT inv FROM users WHERE uid = ?", (uid,)).fetchone()
    if not user:
        return
    inv = float(user['inv'] or 0.0)
    new_rank = "Tiffany"
    for rank, cfg in RANKS_CONFIG.items():
        if inv >= cfg['min_p']:
            new_rank = rank
    conn.execute("UPDATE users SET rank = ? WHERE uid = ?", (new_rank, uid))

def calculate_team_investment(conn, uid):
    total = 0.0
    refs = conn.execute("SELECT uid, inv FROM users WHERE referrer = ?", (uid,)).fetchall()
    for ref in refs:
        total += float(ref['inv'] or 0.0)
        total += calculate_team_investment(conn, ref['uid'])
    return total

COIN_FAVICON = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='%23ef4444'/><circle cx='50' cy='50' r='40' fill='%232b1442'/><text x='50%' y='55%' dominant-baseline='middle' text-anchor='middle' fill='%23ef4444' font-family='sans-serif' font-weight='900' font-size='32'>B4U</text></svg>"

INDEX_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>B4U SOVEREIGN EMPIRE</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>body { background:#0b0312; color:white; font-family:sans-serif; text-align:center; padding:50px; }a { color:#ef4444; margin:15px; text-decoration:none; font-weight:bold; font-size:18px; }</style></head><body><h1>🛡️ B4U SOVEREIGN EMPIRE</h1><p>Next-Gen High Frequency Staking & Empire Platform</p><a href="/login">Login</a> | <a href="/register">Register</a></body></html>"""

REGISTER_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>JOIN B4U EMPIRE</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>body { background:#0b0312; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; }.card { background:#160624; border:1px solid #3c1b5d; border-top:4px solid #ef4444; padding:30px; border-radius:15px; width:340px; }input { width:100%; padding:10px; margin:10px 0; background:#05010a; border:1px solid #4a256d; border-radius:6px; color:white; box-sizing:border-box; }button { width:100%; padding:11px; background:#ef4444; border:none; color:white; font-weight:bold; border-radius:6px; cursor:pointer; font-size:15px; }.err { color:#ff4d4d; font-size:13px; margin-bottom:10px; }</style></head><body><div class="card"><h2 style="color:#ef4444; margin-top:0;">REGISTER NODE</h2>{% if error %}<div class="err">{{ error }}</div>{% endif %}<form action="/register" method="POST"><input type="text" name="name" placeholder="Full Name" required><input type="email" name="email" placeholder="Email Address" required><input type="password" name="password" placeholder="Password" required><input type="text" name="referrer" placeholder="Referral Code (Optional)" value="{{ ref }}"><button type="submit">CREATE ACCOUNT ($100 BONUS)</button></form><br><a href="/login" style="color:#a78bfa; text-decoration:none; font-size:13px;">Already registered? Login</a></div></body></html>"""

LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>LOGIN - B4U EMPIRE</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>body { background:#0b0312; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0; }.card { background:#160624; border:1px solid #3c1b5d; border-top:4px solid #ef4444; padding:30px; border-radius:15px; width:340px; }input { width:100%; padding:10px; margin:10px 0; background:#05010a; border:1px solid #4a256d; border-radius:6px; color:white; box-sizing:border-box; }button { width:100%; padding:11px; background:#ef4444; border:none; color:white; font-weight:bold; border-radius:6px; cursor:pointer; font-size:15px; }.err { color:#ff4d4d; font-size:13px; margin-bottom:10px; }</style></head><body><div class="card"><h2 style="color:#ef4444; margin-top:0;">NODE ACCESS</h2>{% if error %}<div class="err">{{ error }}</div>{% endif %}<form action="/login" method="POST"><input type="email" name="email" placeholder="Email Address" required><input type="password" name="password" placeholder="Password" required><button type="submit">LOGIN</button></form><br><a href="/register" style="color:#a78bfa; text-decoration:none; font-size:13px;">Need an account? Register</a></div></body></html>"""

DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>DASHBOARD - B4U NETWORK</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>body { background:#0b0312; color:#e9ecef; font-family:sans-serif; margin:0; padding:20px; }.hdr { display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #3c1b5d; padding-bottom:15px; }.grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:15px; margin:20px 0; }.card { background:#160624; border:1px solid #3c1b5d; padding:20px; border-radius:12px; border-left:4px solid #ef4444; }.num { font-size:24px; font-weight:bold; color:white; margin-top:5px; }.box { background:#160624; border:1px solid #3c1b5d; padding:20px; border-radius:12px; margin-bottom:20px; }.btn { padding:10px 16px; background:#ef4444; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer; text-decoration:none; display:inline-block; font-size:13px; }input, select { background:#05010a; border:1px solid #4a256d; color:white; padding:9px; border-radius:6px; margin:5px 0; width:100%; box-sizing:border-box; }.msg { background:rgba(16,185,129,0.2); border:1px solid #10b981; color:#10b981; padding:10px; border-radius:6px; margin-bottom:15px; font-weight:bold; font-size:13px; }</style></head><body><div class="hdr"><h2>👑 WELCOME, {{ user.name.upper() }}</h2><div><span style="background:#3c1b5d; padding:6px 12px; border-radius:20px; color:#fdb913; font-weight:bold; font-size:12px;">RANK: {{ user.rank }}</span> <a href="/logout" class="btn" style="background:#333; margin-left:10px;">LOGOUT</a></div></div>{% if msg %}<div class="msg">✅ {{ msg }}</div>{% endif %}<marquee style="background:#160624; color:#fdb913; padding:8px; border-radius:6px; margin-top:15px; font-weight:bold;">📢 {{ announcement }}</marquee><div class="grid"><div class="card" style="border-left-color:#10b981;"><small style="color:#a78bfa;">ACTIVE INVESTMENT</small><div class="num">${{ "{:,.2f}".format(user.inv) }}</div><small style="color:#10b981;">Daily Staking Active</small></div><div class="card" style="border-left-color:#fdb913;"><small style="color:#a78bfa;">PROFIT WALLET</small><div class="num">${{ "{:,.2f}".format(user.profit_wallet) }}</div></div><div class="card" style="border-left-color:#3b82f6;"><small style="color:#a78bfa;">MY NODE UID</small><div class="num" style="font-size:18px;">{{ user.uid }}</div></div><div class="card" style="border-left-color:#8b5cf6;"><small style="color:#a78bfa;">TEAM INVESTMENT</small><div class="num">${{ "{:,.2f}".format(team_inv) }}</div></div></div><div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:20px;"><div class="box"><h3>📥 Deposit Funds</h3><form action="/deposit" method="POST" enctype="multipart/form-data"><input type="number" step="0.01" name="amount" placeholder="Amount ($)" required><select name="method"><option value="USDT TRC20">USDT (TRC20)</option><option value="Easypaisa/Jazzcash">Easypaisa / Jazzcash</option><option value="Bank Transfer">Bank Transfer</option></select><label style="font-size:12px; color:#a78bfa;">Upload Payment Slip:</label><input type="file" name="proof" required><button type="submit" class="btn" style="margin-top:10px; width:100%;">SUBMIT DEPOSIT SLIP</button></form></div><div class="box"><h3>📤 Withdraw Profit</h3><form action="/withdraw" method="POST"><input type="number" step="0.01" name="amount" placeholder="Amount ($)" required><select name="method"><option value="USDT TRC20">USDT (TRC20)</option><option value="Easypaisa">Easypaisa</option><option value="Jazzcash">Jazzcash</option></select><input type="text" name="address" placeholder="Wallet Address / Mobile No." required><button type="submit" class="btn" style="background:#10b981; margin-top:10px; width:100%;">REQUEST WITHDRAWAL</button></form></div><div class="box"><h3>🔄 P2P Internal Transfer</h3><form action="/p2p" method="POST"><input type="text" name="receiver_uid" placeholder="Receiver Node UID (e.g. B4U1002)" required><input type="number" step="0.01" name="amount" placeholder="Amount ($)" required><button type="submit" class="btn" style="background:#8b5cf6; margin-top:10px; width:100%;">TRANSFER FUNDS</button></form></div></div><div class="box"><h3>🔗 Referral Link</h3><input type="text" readonly value="{{ request.host_url }}register?ref={{ user.uid }}" onclick="this.select();"></div></body></html>"""

@app.route('/')
def index():
    uid = session.get('user_uid')
    if uid:
        return redirect('/dashboard')
    return render_template_string(INDEX_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    ref = request.args.get('ref', '')
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        referrer = request.form.get('referrer', '').strip()

        with get_db() as conn:
            user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if user:
                return render_template_string(REGISTER_HTML, error="Email already exists!", ref=ref)
            
            uid = f"B4U{random.randint(1000, 9999)}"
            pwd_hash = generate_password_hash(password)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn.execute("""
                INSERT INTO users (uid, name, email, password, referrer, inv, profit_wallet, rank, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0.0, 'Tiffany', 'Active', ?)
            """, (uid, name, email, pwd_hash, referrer, SIGNUP_BONUS, now))
            
            update_user_rank(conn, uid)
            conn.commit()

        session['user_uid'] = uid
        return redirect('/dashboard?msg=Welcome! $100 Sign-up bonus added to your Active Investment.')

    return render_template_string(REGISTER_HTML, error=None, ref=ref)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user and check_password_hash(user['password'], password):
                if user['status'] != 'Active':
                    return render_template_string(LOGIN_HTML, error="Account is suspended! Contact support.")
                session['user_uid'] = user['uid']
                return redirect('/dashboard')
            return render_template_string(LOGIN_HTML, error="Invalid Email or Password!")
            
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/dashboard')
def dashboard():
    uid = session.get('user_uid')
    if not uid:
        return redirect('/login')

    msg = request.args.get('msg')
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
        if not user:
            session.clear()
            return redirect('/login')
        team_inv = calculate_team_investment(conn, uid)
        ann = conn.execute("SELECT value FROM settings WHERE key='announcement'").fetchone()

    ann_text = ann['value'] if ann else '🚀 Welcome to B4U Sovereign Empire!'
    return render_template_string(DASHBOARD_HTML, user=user, team_inv=team_inv, announcement=ann_text, msg=msg)

@app.route('/deposit', methods=['POST'])
def deposit():
    uid = session.get('user_uid')
    if not uid: return redirect('/login')
    
    amount = float(request.form.get('amount') or 0)
    method = request.form.get('method')
    file = request.files.get('proof')

    if amount <= 0 or not file or not allowed_file(file.filename):
        return redirect('/dashboard?msg=Invalid deposit details or proof file format!')

    filename = secure_filename(f"{uid}_{int(datetime.now().timestamp())}_{file.filename}")
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute("INSERT INTO deposits (uid, amount, method, proof_file, created_at) VALUES (?, ?, ?, ?, ?)",
                     (uid, amount, method, filename, now))
        conn.commit()

    return redirect('/dashboard?msg=Deposit slip submitted! Pending Admin verification.')

@app.route('/withdraw', methods=['POST'])
def withdraw():
    uid = session.get('user_uid')
    if not uid: return redirect('/login')

    amount = float(request.form.get('amount') or 0)
    method = request.form.get('method')
    address = request.form.get('address')

    with get_db() as conn:
        user = conn.execute("SELECT profit_wallet FROM users WHERE uid = ?", (uid,)).fetchone()
        if not user or float(user['profit_wallet']) < amount or amount <= 0:
            return redirect('/dashboard?msg=Insufficient Profit Wallet balance!')

        conn.execute("UPDATE users SET profit_wallet = round(profit_wallet - ?, 2) WHERE uid = ?", (amount, uid))
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO withdrawals (uid, amount, method, address, created_at) VALUES (?, ?, ?, ?, ?)",
                     (uid, amount, method, address, now))
        conn.commit()

    return redirect('/dashboard?msg=Withdrawal request submitted successfully!')

@app.route('/p2p', methods=['POST'])
def p2p():
    uid = session.get('user_uid')
    if not uid: return redirect('/login')

    receiver_uid = request.form.get('receiver_uid', '').strip()
    amount = float(request.form.get('amount') or 0)

    if receiver_uid == uid or amount <= 0:
        return redirect('/dashboard?msg=Invalid recipient or amount!')

    with get_db() as conn:
        sender = conn.execute("SELECT profit_wallet FROM users WHERE uid = ?", (uid,)).fetchone()
        receiver = conn.execute("SELECT uid FROM users WHERE uid = ?", (receiver_uid,)).fetchone()

        if not receiver:
            return redirect('/dashboard?msg=Recipient Node UID not found!')
        if float(sender['profit_wallet']) < amount:
            return redirect('/dashboard?msg=Insufficient Profit Wallet balance!')

        conn.execute("UPDATE users SET profit_wallet = round(profit_wallet - ?, 2) WHERE uid = ?", (amount, uid))
        conn.execute("UPDATE users SET profit_wallet = round(profit_wallet + ?, 2) WHERE uid = ?", (amount, receiver_uid))
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO p2p_transfers (sender_uid, receiver_uid, amount, created_at) VALUES (?, ?, ?, ?)",
                     (uid, receiver_uid, amount, now))
        conn.commit()

    return redirect(f'/dashboard?msg=Transferred ${amount} to {receiver_uid} successfully!')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50001, debug=False)
