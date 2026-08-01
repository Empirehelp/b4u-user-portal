import os
import json
from flask import Flask, request, redirect, url_for, render_template_string, session

user_app = Flask('user_app')
user_app.secret_key = 'b4u_empire_shadow_sovereign_gate_ultra_secure_user_2026'

DB_FILE = "database.json"

RANKS_CONFIG = {
    "Tiffany": {"min_p": 10, "max_p": 699, "min_t": 0, "ib": [0.03, 0.02, 0.01, 0.00, 0.00], "pb": [0.03, 0.01, 0.01, 0.00, 0.00]},
    "Blue Moon": {"min_p": 700, "max_p": 2999, "min_t": 5000, "ib": [0.07, 0.03, 0.01, 0.00, 0.00], "pb": [0.05, 0.03, 0.01, 0.00, 0.00]},
    "Aurora": {"min_p": 3000, "max_p": 9999, "min_t": 30000, "ib": [0.10, 0.03, 0.01, 0.01, 0.01], "pb": [0.07, 0.03, 0.01, 0.01, 0.01]},
    "Cullinan": {"min_p": 10000, "max_p": 29999, "min_t": 100000, "ib": [0.10, 0.05, 0.03, 0.01, 0.01], "pb": [0.08, 0.05, 0.03, 0.01, 0.01]},
    "Sancy": {"min_p": 30000, "max_p": 49999, "min_t": 500000, "ib": [0.12, 0.05, 0.03, 0.03, 0.03], "pb": [0.10, 0.05, 0.03, 0.03, 0.03]},
    "KohiNoor": {"min_p": 50000, "max_p": 1000000, "min_t": 1000000, "ib": [0.15, 0.07, 0.03, 0.03, 0.03], "pb": [0.12, 0.05, 0.03, 0.03, 0.03]}
}

def load_db():
    if not os.path.exists(DB_FILE):
        default_db = {"users": {}, "deposits": [], "withdrawals": [], "p2p_transfers": []}
        with open(DB_FILE, 'w') as f:
            json.dump(default_db, f, indent=4)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def calculate_team_investment(uid, users):
    total = 0.0
    for u_id, u_data in users.items():
        if u_data.get('referrer') == uid:
            total += float(u_data.get('inv', 0.0))
            total += calculate_team_investment(u_id, users)
    return total

def get_detailed_downline(uid, users, level=1):
    downline_entries = []
    for u_id, u_data in users.items():
        if u_data.get('referrer') == uid:
            entry = {
                "uid": u_id,
                "name": u_data.get('name'),
                "level": level,
                "inv": u_data.get('inv', 0.0),
                "status": u_data.get('status', 'Active')
            }
            downline_entries.append(entry)
            downline_entries.extend(get_detailed_downline(u_id, users, level + 1))
    return downline_entries

def auto_upgrade_rank(uid, db):
    user = db["users"][uid]
    p_inv = float(user.get("inv", 0.0))
    t_inv = calculate_team_investment(uid, db["users"])
    matched_rank = "Tiffany"
    for r_name, conf in RANKS_CONFIG.items():
        if p_inv >= conf["min_p"] and t_inv >= conf["min_t"]:
            matched_rank = r_name
    user["rank"] = matched_rank

LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>B4U EMPIRE - MEMBER LOGIN</title><style>body { background: #090312; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }.card { background: rgba(22, 10, 38, 0.9); border: 1px solid #00f2fe; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 0 20px rgba(0,242,254,0.3); width: 300px; }input { padding: 10px; width: 90%; background: #000; border: 1px solid #00f2fe; color: #fff; border-radius: 5px; margin-bottom: 15px; outline: none; }button { background: #00f2fe; color: #000; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; cursor: pointer; width: 100%; }</style></head><body><div class="card"><h2>🚀 B4U LOGIN</h2><form action="/login" method="POST"><input type="text" name="uid" placeholder="User ID (e.g. B4U1001)" required><input type="password" name="password" placeholder="Password" required><button type="submit">LOGIN</button></form></div></body></html>"""

DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>B4U EMPIRE - USER DASHBOARD</title><style>body { background: #090312; color: #e0e6ed; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; }h1 { color: #fdb913; display: flex; justify-content: space-between; align-items: center; font-size: 1.3rem; }.card { background: rgba(22, 10, 38, 0.8); border: 1px solid rgba(0, 242, 254, 0.3); border-radius: 10px; padding: 15px; margin-bottom: 15px; }button, .btn { background: #00f2fe; color: #000; border: none; padding: 8px 15px; border-radius: 5px; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-block; font-size: 12px; }input, select { background: #000; color: #fff; border: 1px solid rgba(0,242,254,0.3); padding: 8px; border-radius: 5px; margin-bottom: 10px; width: 100%; box-sizing: border-box; }</style></head><body><h1><span>Welcome, {{ user.name }} ({{ uid }})</span><a href="/logout" style="color: #ef4444; font-size: 12px; border: 1px solid #ef4444; padding: 4px 10px; border-radius: 5px; text-decoration:none;">LOGOUT</a></h1><div class="card"><h3>📊 Account Overview</h3><p><b>Rank:</b> <span style="color: #fdb913;">{{ user.rank }}</span></p><p><b>Own Investment:</b> ${{ user.inv }}</p><p><b>Team Volume:</b> ${{ team_volume }}</p><p><b>Cash Wallet:</b> ${{ user.cash }}</p><p><b>Profit Wallet:</b> <span style="color: #10b981;">${{ user.profit_wallet }}</span></p></div><div class="card"><h3>📥 Deposit Funds</h3><form action="/deposit" method="POST"><select name="method"><option value="USDT">USDT (TRC20)</option><option value="Bitcoin">Bitcoin</option></select><input type="text" name="tid" placeholder="Transaction Hash / ID" required><input type="number" step="0.01" name="amount" placeholder="Amount ($)" required><button type="submit">Submit Deposit</button></form></div><div class="card"><h3>📤 Withdraw Funds</h3><form action="/withdraw" method="POST"><input type="text" name="method" placeholder="Method (e.g. USDT)" required><input type="text" name="address" placeholder="Wallet Address" required><input type="number" step="0.01" name="amount" placeholder="Amount ($)" required><button type="submit">Request Withdrawal</button></form></div><div class="card"><h3>👥 My Downline Tree</h3><ul>{% for child in downline %}<li><b>{{ child.uid }}</b> - {{ child.name }} (Level {{ child.level }}) - Invested: ${{ child.inv }}</li>{% else %}<li>No team members yet.</li>{% endfor %}</ul></div></body></html>"""

@user_app.route('/')
def home():
    if not session.get('user_uid'):
        return LOGIN_HTML
    return redirect('/dashboard')

@user_app.route('/login', methods=['POST'])
def login():
    db = load_db()
    uid = request.form.get('uid')
    password = request.form.get('password')
    if uid in db["users"] and db["users"][uid].get("password") == password:
        session['user_uid'] = uid
        return redirect('/dashboard')
    return "❌ Invalid Credentials. <a href='/'>Retry</a>"

@user_app.route('/logout')
def logout():
    session.pop('user_uid', None)
    return redirect('/')

@user_app.route('/dashboard')
def dashboard():
    uid = session.get('user_uid')
    if not uid:
        return redirect('/')
    db = load_db()
    if uid not in db["users"]:
        session.pop('user_uid', None)
        return redirect('/')
    auto_upgrade_rank(uid, db)
    save_db(db)
    user = db["users"][uid]
    team_volume = calculate_team_investment(uid, db["users"])
    downline = get_detailed_downline(uid, db["users"])
    return render_template_string(DASHBOARD_HTML, user=user, uid=uid, team_volume=team_volume, downline=downline)

@user_app.route('/deposit', methods=['POST'])
def deposit():
    uid = session.get('user_uid')
    if not uid: return redirect('/')
    db = load_db()
    dep_id = len(db.get("deposits", [])) + 1
    new_dep = {
        "id": dep_id,
        "uid": uid,
        "method": request.form.get('method'),
        "tid": request.form.get('tid'),
        "amount": float(request.form.get('amount') or 0),
        "status": "Pending Verification"
    }
    db.setdefault("deposits", []).append(new_dep)
    save_db(db)
    return redirect('/dashboard')

@user_app.route('/withdraw', methods=['POST'])
def withdraw():
    uid = session.get('user_uid')
    if not uid: return redirect('/')
    db = load_db()
    amount = float(request.form.get('amount') or 0)
    user = db["users"][uid]
    if float(user.get("profit_wallet", 0)) < amount:
        return "❌ Insufficient funds in profit wallet. <a href='/dashboard'>Back</a>"
    user["profit_wallet"] = round(float(user["profit_wallet"]) - amount, 2)
    wit_id = len(db.get("withdrawals", [])) + 1
    new_wit = {
        "id": wit_id,
        "uid": uid,
        "method": request.form.get('method'),
        "address": request.form.get('address'),
        "amount": amount,
        "status": "Pending Processing"
    }
    db.setdefault("withdrawals", []).append(new_wit)
    save_db(db)
    return redirect('/dashboard')

if __name__ == '__main__':
    user_app.run(host='0.0.0.0', port=5000)
