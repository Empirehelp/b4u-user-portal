import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, redirect, render_template_string, session, send_from_directory

admin_app = Flask('admin_app')
admin_app.secret_key = os.environ.get('SECRET_KEY', 'b4u_empire_shadow_sovereign_gate_2026')

DB_FILE = "database.db"
UPLOAD_FOLDER = 'uploads'
admin_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    btc_usd = 68500.0
    b4u_in_btc = f"{coin_price / btc_usd:.8f}"
    return coin_price, coin_change, total_inv, btc_usd, b4u_in_btc

COIN_FAVICON = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='%23fdb913'/><circle cx='50' cy='50' r='40' fill='%232b1442'/><text x='50%' y='55%' dominant-baseline='middle' text-anchor='middle' fill='%23fdb913' font-family='sans-serif' font-weight='900' font-size='30'>$</text></svg>"

BIG_COIN_SVG = """<div style="position: relative; display: inline-block;"><div style="position: absolute; width: 100px; height: 100px; background: radial-gradient(circle, rgba(253,185,19,0.4) 0%, rgba(43,20,66,0) 70%); border-radius: 50%; top:-10px; left:-10px; animation: pulse 2s infinite alternate;"></div><svg width="85" height="85" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0px 0px 15px rgba(253, 185, 19, 0.8));"><defs><linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ffe259" /><stop offset="100%" stop-color="#ffa751" /></linearGradient><linearGradient id="purpleBg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#3c1b5d" /><stop offset="100%" stop-color="#180729" /></linearGradient></defs><circle cx="50" cy="50" r="48" fill="url(#goldGrad)" stroke="#fff" stroke-width="2"/><circle cx="50" cy="50" r="40" fill="url(#purpleBg)" stroke="#fdb913" stroke-width="2"/><text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle" fill="#fdb913" font-family="'Segoe UI', sans-serif" font-weight="900" font-size="34">$</text><text x="50%" y="73%" dominant-baseline="middle" text-anchor="middle" fill="#ffffff" font-family="'Segoe UI', sans-serif" font-weight="900" font-size="10" letter-spacing="1.5">B4U</text></svg></div>"""

SMALL_COIN_SVG = """<svg width="32" height="32" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="48" fill="#fdb913"/><circle cx="50" cy="50" r="40" fill="#2b1442"/><text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle" fill="#fdb913" font-family="sans-serif" font-weight="900" font-size="30">$</text></svg>"""

ADMIN_LOGIN_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ADMIN CONSOLE - B4U NETWORK</title>
<link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml">
<style>
  body { background: #140620; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
  .login-card { background: #2b1442; border-top: 5px solid #fdb913; padding: 40px 35px; border-radius: 16px; width: 340px; box-shadow: 0 15px 35px rgba(0,0,0,0.6); text-align: center; }
  h2 { color: #fdb913; font-size: 20px; margin-top: 15px; font-weight: 800; letter-spacing: 1px; margin-bottom: 25px; }
  input { width: 100%; padding: 12px; background: #10041a; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 18px; box-sizing: border-box; outline:none; font-size:14px; }
  input:focus { border-color: #fdb913; box-shadow: 0 0 8px rgba(253, 185, 19, 0.3); }
  button { width: 100%; padding: 12px; background: linear-gradient(135deg, #fdb913, #e28700); border: none; font-weight: bold; cursor: pointer; border-radius: 8px; color: #1a0928; font-size: 15px; letter-spacing:1px; transition: 0.3s; }
  button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(253, 185, 19, 0.4); }
  .err { color: #ff4d4d; font-size: 13px; margin-bottom: 15px; background: rgba(255,77,77,0.1); padding: 8px; border-radius: 6px; }
</style>
</head>
<body>
<div class="login-card">
  """ + BIG_COIN_SVG + """
  <h2>B4U SOVEREIGN ADMIN</h2>
  {% if error %}<div class="err">{{ error }}</div>{% endif %}
  <form action="/login" method="POST">
    <input type="password" name="password" placeholder="System Security Passcode" required>
    <button type="submit">UNLOCK TERMINAL</button>
  </form>
</div>
</body>
</html>"""

ADMIN_DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ADMIN DASHBOARD - B4U NETWORK</title>
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
</style>
</head>
<body>
<h1>
  <div class="brand-head">""" + SMALL_COIN_SVG + """<span class="brand-title">B4U ADMIN SYSTEM TERMINAL</span></div>
  <div><a href="/logout" class="logout-btn">LOGOUT</a></div>
</h1>

<div class="trading-hero">
  <div class="hero-left">
    """ + BIG_COIN_SVG + """
    <div>
      <div class="coin-details-title">B4U COIN Engine <span class="pair-badge">B4U / BTC</span></div>
      <div class="sub-tag">⚡ Network Capitalization & Automated Minting Value</div>
    </div>
  </div>
  <div class="trading-metrics">
    <div class="metric-box">
      <div class="metric-label">BITCOIN BENCHMARK</div>
      <div class="metric-val" style="color: #f59e0b;">${{ "{:,.2f}".format(btc_usd) }}</div>
    </div>
    <div class="metric-box">
      <div class="metric-label">TOTAL SYSTEM CAPITAL</div>
      <div class="metric-val">${{ "{:,.2f}".format(total_inv) }}</div>
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
    <small style="color:#a78bfa;">TOTAL REGISTERED NODES</small>
    <div class="stat-num" style="color:#fdb913;">{{ users|length }} Users</div>
  </div>
  <div class="stat-card" style="border-left: 4px solid #10b981;">
    <small style="color:#a78bfa;">PENDING DEPOSITS</small>
    <div class="stat-num">{{ pending_deps|length }} Requests</div>
  </div>
  <div class="stat-card" style="border-left: 4px solid #ef4444;">
    <small style="color:#a78bfa;">PENDING WITHDRAWALS</small>
    <div class="stat-num">{{ pending_wits|length }} Requests</div>
  </div>
</div>

<div class="box">
  <h2>👤 Registered Network Members</h2>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>UID</th>
          <th>Name</th>
          <th>Inv ($)</th>
          <th>Rank</th>
          <th>Profit ($)</th>
          <th>Referrer</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {% for u in users %}
        <tr>
          <td><b>{{ u.uid }}</b></td>
          <td>{{ u.name }}</td>
          <td>${{ u.inv }}</td>
          <td><span style="color:#fdb913; font-weight:bold;">{{ u.rank }}</span></td>
          <td>${{ u.profit_wallet }}</td>
          <td>{{ u.referrer or 'None' }}</td>
          <td>{% if u.status == 'Active' %}<span style="color:#10b981; font-weight:bold;">Active</span>{% else %}<span style="color:#ef4444; font-weight:bold;">Suspended</span>{% endif %}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<div class="box">
  <h2>📥 Deposit Approval Queue</h2>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>User UID</th>
          <th>Method</th>
          <th>Amount</th>
          <th>Proof Slip</th>
          <th>Status</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {% for d in pending_deps %}
        <tr>
          <td>#{{ d.id }}</td>
          <td><b>{{ d.uid }}</b></td>
          <td>{{ d.method }}</td>
          <td><b>${{ d.amount }}</b></td>
          <td>{% if d.proof_file %}<a href="/uploads/{{ d.proof_file }}" target="_blank" style="color:#fdb913; font-weight:bold;">View Proof</a>{% else %}<span style="color:#666;">No File</span>{% endif %}</td>
          <td><i>{{ d.status }}</i></td>
          <td>
            <form action="/approve_deposit" method="POST" style="display:inline;">
              <input type="hidden" name="dep_id" value="{{ d.id }}">
              <button type="submit" class="btn" style="padding: 4px 10px; font-size:11px;">APPROVE</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<div class="box">
  <h2>📤 Withdrawal Approval Queue</h2>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>User UID</th>
          <th>Method</th>
          <th>Address</th>
          <th>Amount</th>
          <th>Status</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {% for w in pending_wits %}
        <tr>
          <td>#{{ w.id }}</td>
          <td><b>{{ w.uid }}</b></td>
          <td>{{ w.method }}</td>
          <td><code>{{ w.address }}</code></td>
          <td><b>${{ w.amount }}</b></td>
          <td><i>{{ w.status }}</i></td>
          <td>
            <form action="/approve_withdrawal" method="POST" style="display:inline;">
              <input type="hidden" name="wit_id" value="{{ w.id }}">
              <button type="submit" class="btn" style="background: linear-gradient(135deg, #3b82f6, #2563eb); padding: 4px 10px; font-size:11px;">APPROVE</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

</body>
</html>"""

@admin_app.route('/')
def admin_dashboard():
    if not session.get('admin_logged'):
        return render_template_string(ADMIN_LOGIN_HTML, error=None)
    with get_db() as conn:
        users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
        pending_deps = conn.execute("SELECT * FROM deposits WHERE status LIKE '%Pending%' ORDER BY id DESC").fetchall()
        pending_wits = conn.execute("SELECT * FROM withdrawals WHERE status LIKE '%Pending%' ORDER BY id DESC").fetchall()
        coin_price, coin_change, total_inv, btc_usd, b4u_in_btc = get_coin_price()
    return render_template_string(ADMIN_DASHBOARD_HTML, users=users, pending_deps=pending_deps, pending_wits=pending_wits, coin_price=coin_price, coin_change=coin_change, total_inv=total_inv, btc_usd=btc_usd, b4u_in_btc=b4u_in_btc)

@admin_app.route('/login', methods=['POST'])
def admin_login():
    passcode = request.form.get('password')
    if passcode == "admin123":
        session['admin_logged'] = True
        return redirect('/')
    return render_template_string(ADMIN_LOGIN_HTML, error="Invalid Admin Passcode!")

@admin_app.route('/logout')
def admin_logout():
    session.clear()
    return redirect('/')

@admin_app.route('/approve_deposit', methods=['POST'])
def approve_deposit():
    if not session.get('admin_logged'): 
        return redirect('/')
    dep_id = request.form.get('dep_id')
    with get_db() as conn:
        dep = conn.execute("SELECT * FROM deposits WHERE id = ?", (dep_id,)).fetchone()
        if dep and 'Pending' in dep['status']:
            conn.execute("UPDATE deposits SET status = '✅ Approved' WHERE id = ?", (dep_id,))
            conn.execute("UPDATE users SET inv = round(inv + ?, 2) WHERE uid = ?", (dep['amount'], dep['uid']))
            conn.commit()
    return redirect('/')

@admin_app.route('/approve_withdrawal', methods=['POST'])
def approve_withdrawal():
    if not session.get('admin_logged'): 
        return redirect('/')
    wit_id = request.form.get('wit_id')
    with get_db() as conn:
        wit = conn.execute("SELECT * FROM withdrawals WHERE id = ?", (wit_id,)).fetchone()
        if wit and 'Pending' in wit['status']:
            conn.execute("UPDATE withdrawals SET status = '✅ Approved & Sent' WHERE id = ?", (wit_id,))
            conn.commit()
    return redirect('/')

@admin_app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(admin_app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    admin_app.run(host='0.0.0.0', port=50002, debug=False)
