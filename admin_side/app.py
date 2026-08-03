import os
import sqlite3
from datetime import datetime
from flask import Flask, request, redirect, render_template_string, session, send_from_directory

admin_app = Flask('admin_app')
admin_app.secret_key = os.environ.get('SECRET_KEY', 'b4u_empire_admin_sovereign_gate_2026')
DB_FILE = "database.db"
UPLOAD_FOLDER = '../user_side/uploads'
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

with get_db() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('announcement', '🚀 Welcome to B4U Sovereign Empire! Daily Staking Rewards are Live.')")
    conn.commit()

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

COIN_FAVICON = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='%23ef4444'/><circle cx='50' cy='50' r='40' fill='%232b1442'/><text x='50%' y='55%' dominant-baseline='middle' text-anchor='middle' fill='%23ef4444' font-family='sans-serif' font-weight='900' font-size='28'>ADM</text></svg>"

ADMIN_LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>ADMIN PORTAL - B4U NETWORK</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>body { background: #0b0312; color: #e9ecef; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }.login-card { background: linear-gradient(145deg, #1f072e, #0e0217); border-top: 5px solid #ef4444; padding: 40px; border-radius: 20px; width: 340px; text-align: center; }input { width: 100%; padding: 12px; background: #05010a; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 18px; box-sizing: border-box; }button { width: 100%; padding: 13px; background: #ef4444; border: none; font-weight: bold; cursor: pointer; border-radius: 8px; color: white; }</style></head><body><div class="login-card"><h2 style="color:#ef4444;">🛡️ ADMIN ACCESS</h2>{% if error %}<div style="color:red; margin-bottom:10px;">{{ error }}</div>{% endif %}<form action="/admin/login" method="POST"><input type="text" name="username" placeholder="Admin Username" required><input type="password" name="password" placeholder="Master Key" required><button type="submit">LOGIN TO DASHBOARD</button></form></div></body></html>"""

ADMIN_DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>MASTER CONTROL - B4U EMPIRE</title><link rel="icon" href='""" + COIN_FAVICON + """' type="image/svg+xml"><style>body { background-color: #0b0312; color: #e9ecef; font-family: sans-serif; margin: 0; padding: 22px; }h1 { color: #ef4444; border-bottom: 2px solid #3c1b5d; padding-bottom: 15px; display: flex; justify-content: space-between; font-size: 1.4rem; }.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 25px; }.stat-card { background: #160624; border: 1px solid #3c1b5d; border-radius: 12px; padding: 18px; text-align: center; }.stat-num { font-size: 22px; font-weight: bold; color: white; margin-top: 5px; }.box { background: #160624; padding: 22px; border-radius: 14px; margin-bottom: 25px; border-top: 4px solid #ef4444; border-left: 1px solid #3c1b5d; border-right: 1px solid #3c1b5d; border-bottom: 1px solid #3c1b5d; }.table-wrapper { width: 100%; overflow-x: auto; background: #05010a; margin-top: 15px; border-radius: 10px; }table { width: 100%; border-collapse: collapse; min-width: 700px; }th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #1c0a2a; font-size: 13px; }th { background-color: #0d0414; color: #ef4444; }.form-inline { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }input, select { background: #05010a; color: white; border: 1px solid #4a256d; padding: 10px; border-radius: 6px; outline: none; font-size: 13px; }.btn-action { padding: 6px 12px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 11px; text-decoration: none; display: inline-block; }.btn-approve { background: #10b981; color: white; }.btn-reject { background: #ef4444; color: white; }.btn-activate { background: #3b82f6; color: white; }.logout-btn { background: #ef4444; color: white; text-decoration: none; padding: 7px 16px; border-radius: 6px; font-size: 12px; font-weight: bold; }.msg-alert { background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; color: #10b981; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; font-weight: bold; }</style></head><body><h1><span>🛡️ B4U SYSTEM MASTER DASHBOARD</span><a href="/admin/logout" class="logout-btn">LOGOUT</a></h1>{% if msg %}<div class="msg-alert">✅ {{ msg }}</div>{% endif %}

<div class="stats-grid"><div class="stat-card" style="border-left: 4px solid #10b981;"><small style="color:#a78bfa;">TOTAL REGISTERED NODES</small><div class="stat-num">{{ stats.total_users }}</div></div><div class="stat-card" style="border-left: 4px solid #fdb913;"><small style="color:#a78bfa;">TOTAL INVESTMENTS</small><div class="stat-num">${{ "{:,.2f}".format(stats.total_inv) }}</div></div><div class="stat-card" style="border-left: 4px solid #ef4444;"><small style="color:#a78bfa;">PENDING DEPOSITS</small><div class="stat-num">{{ stats.pending_deposits }}</div></div><div class="stat-card" style="border-left: 4px solid #3b82f6;"><small style="color:#a78bfa;">PENDING WITHDRAWALS</small><div class="stat-num">{{ stats.pending_withdrawals }}</div></div></div>

<div class="box" style="border-top-color: #10b981;"><h2>⚡ Distribute Daily Investment Profit (ROI)</h2><form action="/admin/distribute_profit" method="POST" class="form-inline"><input type="number" step="0.01" name="percentage" placeholder="Daily Profit Rate % (e.g. 1.5)" required style="width:220px;"><button type="submit" class="btn-action btn-approve" style="padding:10px 20px;">DISTRIBUTE DAILY PROFIT TO ALL USERS</button></form></div>

<div class="box" style="border-top-color: #fdb913;"><h2>📢 Broadcast Announcement</h2><form action="/admin/update_announcement" method="POST" class="form-inline"><input type="text" name="announcement" value="{{ announcement }}" placeholder="System Announcement" required style="flex:1;"><button type="submit" class="btn-action btn-approve" style="padding:10px 20px;">UPDATE TICKER</button></form></div>

<div class="box" style="border-top-color: #8b5cf6;"><h2>💰 Direct User Wallet Credit / Adjustment</h2><form action="/admin/adjust_wallet" method="POST" class="form-inline"><input type="text" name="uid" placeholder="Node UID (e.g. B4U1001)" required><select name="wallet_type"><option value="profit_wallet">Profit Wallet</option><option value="inv">Active Investment</option></select><input type="number" step="0.01" name="amount" placeholder="Amount ($)" required><select name="type"><option value="add">Add (+)</option><option value="deduct">Deduct (-)</option></select><button type="submit" class="btn-action btn-activate" style="padding:10px 20px;">EXECUTE ADJUSTMENT</button></form></div>

<div class="box"><h2>📥 Pending Deposit Requests & Proof Slips</h2><div class="table-wrapper"><table><thead><tr><th>ID</th><th>Node UID</th><th>Amount</th><th>Method</th><th>Proof Slip</th><th>Actions</th></tr></thead><tbody>{% for dep in deposits %}<tr><td>#{{ dep.id }}</td><td><code>{{ dep.uid }}</code></td><td><b>${{ dep.amount }}</b></td><td>{{ dep.method }}</td><td>{% if dep.proof_file %}<a href="/uploads/{{ dep.proof_file }}" target="_blank" style="color:#fdb913; font-weight:bold;">View Proof</a>{% else %}<span style="color:#666;">No File</span>{% endif %}</td><td><a href="/admin/approve_deposit/{{ dep.id }}" class="btn-action btn-approve">APPROVE & ADD CAPITAL</a><a href="/admin/reject_deposit/{{ dep.id }}" class="btn-action btn-reject">REJECT</a></td></tr>{% else %}<tr><td colspan="6" style="text-align:center; color:#a78bfa;">No pending deposits.</td></tr>{% endfor %}</tbody></table></div></div>

<div class="box"><h2>📤 Pending Withdrawal Requests</h2><div class="table-wrapper"><table><thead><tr><th>ID</th><th>Node UID</th><th>Amount</th><th>Method</th><th>Account / Address</th><th>Actions</th></tr></thead><tbody>{% for wit in withdrawals %}<tr><td>#{{ wit.id }}</td><td><code>{{ wit.uid }}</code></td><td><b>${{ wit.amount }}</b></td><td>{{ wit.method }}</td><td><code>{{ wit.address }}</code></td><td><a href="/admin/approve_withdraw/{{ wit.id }}" class="btn-action btn-approve">APPROVE WITHDRAWAL</a><a href="/admin/reject_withdraw/{{ wit.id }}" class="btn-action btn-reject">REJECT & REFUND</a></td></tr>{% else %}<tr><td colspan="6" style="text-align:center; color:#a78bfa;">No pending withdrawal requests.</td></tr>{% endfor %}</tbody></table></div></div>

<div class="box"><h2>👥 Network Users Management</h2><div class="table-wrapper"><table><thead><tr><th>Node UID</th><th>Name</th><th>Email</th><th>Investment</th><th>Profit Wallet</th><th>Rank</th><th>Status</th><th>Actions</th></tr></thead><tbody>{% for u in users %}<tr><td><code>{{ u.uid }}</code></td><td>{{ u.name }}</td><td>{{ u.email }}</td><td><b>${{ u.inv }}</b></td><td>${{ u.profit_wallet }}</td><td><span style="color:#fdb913;">{{ u.rank }}</span></td><td><b>{{ u.status }}</b></td><td>{% if u.status == 'Active' %}<a href="/admin/toggle_status/{{ u.uid }}" class="btn-action btn-reject">SUSPEND</a>{% else %}<a href="/admin/toggle_status/{{ u.uid }}" class="btn-action btn-activate">ACTIVATE</a>{% endif %}</td></tr>{% endfor %}</tbody></table></div></div></body></html>"""

@admin_app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            session['admin_logged'] = True
            return redirect('/admin')
        return render_template_string(ADMIN_LOGIN_HTML, error="Invalid Master Admin Credentials!")
    return render_template_string(ADMIN_LOGIN_HTML, error=None)

@admin_app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged'):
        return redirect('/admin/login')
    msg = request.args.get('msg')
    with get_db() as conn:
        users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
        deposits = conn.execute("SELECT * FROM deposits WHERE status LIKE '%Pending%' ORDER BY id DESC").fetchall()
        withdrawals = conn.execute("SELECT * FROM withdrawals WHERE status LIKE '%Pending%' ORDER BY id DESC").fetchall()
        ann = conn.execute("SELECT value FROM settings WHERE key='announcement'").fetchone()
        
        tot_users = conn.execute("SELECT COUNT(id) as cnt FROM users").fetchone()['cnt']
        tot_inv = conn.execute("SELECT SUM(inv) as tot FROM users").fetchone()['tot'] or 0.0

    stats = {
        "total_users": tot_users,
        "total_inv": float(tot_inv),
        "pending_deposits": len(deposits),
        "pending_withdrawals": len(withdrawals)
    }

    return render_template_string(
        ADMIN_DASHBOARD_HTML, 
        users=users, 
        deposits=deposits, 
        withdrawals=withdrawals, 
        stats=stats, 
        announcement=ann['value'] if ann else '',
        msg=msg
    )

@admin_app.route('/admin/distribute_profit', methods=['POST'])
def distribute_profit():
    if not session.get('admin_logged'): 
        return redirect('/admin/login')
    percentage = float(request.form.get('percentage') or 0)
    if percentage <= 0:
        return redirect('/admin?msg=Please specify a valid profit percentage rate!')

    with get_db() as conn:
        # Calculate daily ROI based on each active user's investment balance
        conn.execute("UPDATE users SET profit_wallet = round(profit_wallet + (inv * (? / 100.0)), 2) WHERE status='Active' AND inv > 0", (percentage,))
        conn.commit()

    return redirect(f'/admin?msg=Successfully distributed {percentage}% daily profit to all active accounts!')

@admin_app.route('/admin/update_announcement', methods=['POST'])
def update_announcement():
    if not session.get('admin_logged'): 
        return redirect('/admin/login')
    new_ann = request.form.get('announcement', '').strip()
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('announcement', ?)", (new_ann,))
        conn.commit()
    return redirect('/admin?msg=Broadcast announcement updated successfully!')

@admin_app.route('/admin/adjust_wallet', methods=['POST'])
def adjust_wallet():
    if not session.get('admin_logged'): 
        return redirect('/admin/login')
    uid = request.form.get('uid', '').strip()
    wallet_type = request.form.get('wallet_type')
    amount = float(request.form.get('amount') or 0)
    adj_type = request.form.get('type')
    
    if amount <= 0:
        return redirect('/admin?msg=Invalid amount specified!')

    final_amt = amount if adj_type == 'add' else -amount

    with get_db() as conn:
        user = conn.execute("SELECT id FROM users WHERE uid = ?", (uid,)).fetchone()
        if not user:
            return redirect('/admin?msg=Node UID not found!')
        
        if wallet_type == 'profit_wallet':
            conn.execute("UPDATE users SET profit_wallet = round(profit_wallet + ?, 2) WHERE uid = ?", (final_amt, uid))
        else:
            conn.execute("UPDATE users SET inv = round(inv + ?, 2) WHERE uid = ?", (final_amt, uid))
            update_user_rank(conn, uid)
            
        conn.execute("INSERT INTO deposits (uid, amount, method, status) VALUES (?, ?, ?, '✅ Admin Adjustment')", (uid, abs(final_amt), f'Admin {adj_type.upper()} ({wallet_type})'))
        conn.commit()

    return redirect(f'/admin?msg=Successfully adjusted {wallet_type} for {uid}!')

@admin_app.route('/admin/approve_deposit/<int:dep_id>')
def approve_deposit(dep_id):
    if not session.get('admin_logged'): 
        return redirect('/admin/login')
    with get_db() as conn:
        dep = conn.execute("SELECT * FROM deposits WHERE id = ?", (dep_id,)).fetchone()
        if dep:
            conn.execute("UPDATE deposits SET status = '✅ Approved' WHERE id = ?", (dep_id,))
            conn.execute("UPDATE users SET inv = round(inv + ?, 2) WHERE uid = ?", (dep['amount'], dep['uid']))
            update_user_rank(conn, dep['uid'])
            conn.commit()
    return redirect('/admin?msg=Deposit approved & user investment upgraded!')

@admin_app.route('/admin/reject_deposit/<int:dep_id>')
def reject_deposit(dep_id):
    if not session.get('admin_logged'): 
        return redirect('/admin/login')
    with get_db() as conn:
        conn.execute("UPDATE deposits SET status = '❌ Rejected' WHERE id = ?", (dep_id,))
        conn.commit()
    return redirect('/admin?msg=Deposit request rejected.')

@admin_app.route('/admin/approve_withdraw/<int:wit_id>')
def approve_withdraw(wit_id):
    if not session.get('admin_logged'): 
        return redirect('/admin/login')
    with get_db() as conn:
        conn.execute("UPDATE withdrawals SET status = '✅ Approved' WHERE id = ?", (wit_id,))
        conn.commit()
    return redirect('/admin?msg=Withdrawal request approved!')

@admin_app.route('/admin/reject_withdraw/<int:wit_id>')
def reject_withdraw(wit_id):
    if not session.get('admin_logged'): 
        return redirect('/admin/login')
    with get_db() as conn:
        wit = conn.execute("SELECT * FROM withdrawals WHERE id = ?", (wit_id,)).fetchone()
        if wit:
            conn.execute("UPDATE withdrawals SET status = '❌ Rejected & Refunded' WHERE id = ?", (wit_id,))
            conn.execute("UPDATE users SET profit_wallet = round(profit_wallet + ?, 2) WHERE uid = ?", (wit['amount'], wit['uid']))
            conn.commit()
    return redirect('/admin?msg=Withdrawal rejected & amount refunded to user!')

@admin_app.route('/admin/toggle_status/<uid>')
def toggle_status(uid):
    if not session.get('admin_logged'): 
        return redirect('/admin/login')
    with get_db() as conn:
        user = conn.execute("SELECT status FROM users WHERE uid = ?", (uid,)).fetchone()
        if user:
            new_status = 'Suspended' if user['status'] == 'Active' else 'Active'
            conn.execute("UPDATE users SET status = ? WHERE uid = ?", (new_status, uid))
            conn.commit()
    return redirect(f'/admin?msg=User status updated to {new_status}')

@admin_app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(admin_app.config['UPLOAD_FOLDER'], filename)

@admin_app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin/login')

if __name__ == '__main__':
    admin_app.run(host='0.0.0.0', port=50002, debug=False)
