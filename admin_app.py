import os
import sqlite3
from datetime import datetime
from flask import Flask, request, redirect, render_template_string, session, url_for

admin_app = Flask('admin_app')
app = admin_app
admin_app.secret_key = os.environ.get('SECRET_KEY', 'b4u_empire_admin_sovereign_gate_2026')
DB_FILE = "/tmp/database.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_coin_price():
    with get_db() as conn:
        res = conn.execute("SELECT SUM(inv) as total FROM users").fetchone()
        total_inv = float(res['total'] or 0.0) if res else 0.0
        base_price = 1.00
        price_growth = (total_inv / 1000.0) * 0.05
        coin_price = round(base_price + price_growth, 4)
        coin_change = round(((coin_price - base_price) / base_price) * 100, 2)
        return coin_price, coin_change, total_inv

ADMIN_LOGIN_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ADMIN SOVEREIGN PORTAL - B4U NETWORK</title>
    <style>
        body { background: #0c0414; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: #1c0b2e; border-top: 5px solid #ef4444; padding: 40px; border-radius: 16px; width: 340px; box-shadow: 0 15px 35px rgba(0,0,0,0.8); text-align: center; }
        h2 { color: #ef4444; font-size: 20px; font-weight: 900; letter-spacing: 1px; margin-bottom: 25px; }
        input { width: 100%; padding: 12px; background: #0c0414; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 18px; box-sizing: border-box; outline:none; font-size:14px; }
        input:focus { border-color: #ef4444; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #ef4444, #991b1b); border: none; font-weight: bold; cursor: pointer; border-radius: 8px; color: white; font-size: 15px; letter-spacing:1px; }
        .err { color: #ff4d4d; font-size: 13px; margin-bottom: 15px; background: rgba(255,77,77,0.1); padding: 8px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🛡️ ADMIN CONTROL GATE</h2>
        {% if error %}<div class="err">{{ error }}</div>{% endif %}
        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="Admin Username" required>
            <input type="password" name="password" placeholder="Admin Secret Key" required>
            <button type="submit">AUTHENTICATE ADMIN</button>
        </form>
    </div>
</body>
</html>"""

ADMIN_DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ADMIN DASHBOARD - B4U NETWORK</title>
    <style>
        body { background-color: #0c0414; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #ef4444; border-bottom: 2px solid #3c1b5d; padding-bottom: 10px; display: flex; justify-content: space-between; align-items: center; margin-top:0; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; }
        .card { background: #1c0b2e; border: 1px solid #4a256d; border-radius: 10px; padding: 15px; text-align: center; }
        .card-val { font-size: 24px; font-weight: bold; color: #fdb913; margin-top: 5px; }
        .box { background: #1c0b2e; padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 1px solid #3c1b5d; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
        h2 { color: #fdb913; margin-top: 0; border-bottom: 1px solid #3c1b5d; padding-bottom: 8px; font-size: 16px; font-weight: 700; }
        .table-wrapper { width: 100%; overflow-x: auto; background: #0c0414; border-radius: 8px; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; min-width: 700px; }
        th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #2b1442; font-size: 13px; }
        th { background: #140620; color: #ef4444; font-weight: 700; }
        input, select { background: #0c0414; color: white; border: 1px solid #4a256d; padding: 6px 10px; border-radius: 6px; font-size: 12px; }
        .btn { padding: 6px 12px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; color: white; font-size: 12px; }
        .btn-green { background: #10b981; }
        .btn-red { background: #ef4444; }
        .btn-blue { background: #3b82f6; }
        .logout-btn { background: #ef4444; color: white; text-decoration: none; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: bold; }
        .msg { padding: 10px; border-radius: 6px; background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid #10b981; margin-bottom: 15px; }
    </style>
</head>
<body>
    <h1>
        <span>🛡️ B4U SYSTEM CONTROL PANEL (ADMIN)</span>
        <a href="/logout" class="logout-btn">LOGOUT</a>
    </h1>
    {% if msg %}<div class="msg">{{ msg }}</div>{% endif %}

    <div class="grid">
        <div class="card" style="border-left: 4px solid #fdb913;"><small style="color:#a78bfa">TOTAL NETWORK LIQUIDITY</small><div class="card-val">${{ "{:,.2f}".format(total_inv) }}</div></div>
        <div class="card" style="border-left: 4px solid #10b981;"><small style="color:#a78bfa">B4U TOKEN PRICE</small><div class="card-val">${{ coin_price }}</div></div>
        <div class="card" style="border-left: 4px solid #3b82f6;"><small style="color:#a78bfa">REGISTERED NODES</small><div class="card-val">{{ users|length }}</div></div>
        <div class="card" style="border-left: 4px solid #ef4444;"><small style="color:#a78bfa">PENDING DEPOSITS</small><div class="card-val">{{ pending_deposits|length }}</div></div>
    </div>

    <!-- PENDING DEPOSITS MANAGEMENT -->
    <div class="box">
        <h2>📥 Pending Capital Verification (Deposits)</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr><th>ID</th><th>User UID</th><th>Amount</th><th>Method</th><th>Date</th><th>Action</th></tr>
                </thead>
                <tbody>
                    {% for dep in pending_deposits %}
                    <tr>
                        <td>#{{ dep.id }}</td>
                        <td><code>{{ dep.uid }}</code></td>
                        <td><b style="color:#10b981;">${{ dep.amount }}</b></td>
                        <td>{{ dep.method }}</td>
                        <td>{{ dep.created_at }}</td>
                        <td>
                            <form action="/approve_deposit" method="POST" style="display:inline;">
                                <input type="hidden" name="id" value="{{ dep.id }}">
                                <button type="submit" class="btn btn-green">APPROVE & ADD INVESTMENT</button>
                            </form>
                            <form action="/reject_deposit" method="POST" style="display:inline;">
                                <input type="hidden" name="id" value="{{ dep.id }}">
                                <button type="submit" class="btn btn-red">REJECT</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="6" style="text-align:center; color:#a78bfa;">No pending deposits verification found.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- PENDING WITHDRAWALS MANAGEMENT -->
    <div class="box">
        <h2>📤 Pending Liquidation Requests (Withdrawals)</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr><th>ID</th><th>User UID</th><th>Amount</th><th>Method & Address</th><th>Date</th><th>Action</th></tr>
                </thead>
                <tbody>
                    {% for wit in pending_withdrawals %}
                    <tr>
                        <td>#{{ wit.id }}</td>
                        <td><code>{{ wit.uid }}</code></td>
                        <td><b style="color:#ef4444;">${{ wit.amount }}</b></td>
                        <td><code>{{ wit.method }} - {{ wit.address }}</code></td>
                        <td>{{ wit.created_at }}</td>
                        <td>
                            <form action="/approve_withdrawal" method="POST" style="display:inline;">
                                <input type="hidden" name="id" value="{{ wit.id }}">
                                <button type="submit" class="btn btn-green">APPROVE & COMPLETE</button>
                            </form>
                            <form action="/reject_withdrawal" method="POST" style="display:inline;">
                                <input type="hidden" name="id" value="{{ wit.id }}">
                                <button type="submit" class="btn btn-red">REJECT & REFUND</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="6" style="text-align:center; color:#a78bfa;">No pending withdrawal requests found.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- ALL USERS DIRECT DATABASE EDITOR -->
    <div class="box">
        <h2>👤 System Users & Financial Controls</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr><th>UID</th><th>Name</th><th>Rank</th><th>Investment</th><th>Profit Wallet</th><th>Referrer</th><th>Status</th><th>Update Action</th></tr>
                </thead>
                <tbody>
                    {% for u in users %}
                    <tr>
                        <form action="/update_user" method="POST">
                            <input type="hidden" name="uid" value="{{ u.uid }}">
                            <td><code>{{ u.uid }}</code></td>
                            <td>{{ u.name }}</td>
                            <td>
                                <input type="text" name="rank" value="{{ u.rank }}" style="width:80px;">
                            </td>
                            <td>
                                $<input type="number" step="0.01" name="inv" value="{{ u.inv }}" style="width:80px;">
                            </td>
                            <td>
                                $<input type="number" step="0.01" name="profit_wallet" value="{{ u.profit_wallet }}" style="width:80px;">
                            </td>
                            <td><code>{{ u.referrer or 'None' }}</code></td>
                            <td>
                                <select name="status">
                                    <option value="Active" {% if u.status == 'Active' %}selected{% endif %}>Active</option>
                                    <option value="Suspended" {% if u.status == 'Suspended' %}selected{% endif %}>Suspended</option>
                                </select>
                            </td>
                            <td>
                                <button type="submit" class="btn btn-blue">SAVE UPDATES</button>
                            </td>
                        </form>
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
    if not session.get('admin_logged_in'):
        return render_template_string(ADMIN_LOGIN_HTML, error=None)
    msg = session.pop('flash_msg', None)
    with get_db() as conn:
        users = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
        pending_deposits = conn.execute("SELECT * FROM deposits WHERE status LIKE '%Pending%' ORDER BY id DESC").fetchall()
        pending_withdrawals = conn.execute("SELECT * FROM withdrawals WHERE status LIKE '%Pending%' ORDER BY id DESC").fetchall()
    coin_price, coin_change, total_inv = get_coin_price()
    return render_template_string(
        ADMIN_DASHBOARD_HTML,
        users=users,
        pending_deposits=pending_deposits,
        pending_withdrawals=pending_withdrawals,
        coin_price=coin_price,
        total_inv=total_inv,
        msg=msg
    )

@admin_app.route('/login', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == 'admin' and password in ['admin', 'B4u_empire_2026!']:
        session['admin_logged_in'] = True
        return redirect('/')
    return render_template_string(ADMIN_LOGIN_HTML, error="Invalid Admin Credentials!")

@admin_app.route('/logout')
def admin_logout():
    session.clear()
    return redirect('/')

@admin_app.route('/approve_deposit', methods=['POST'])
def approve_deposit():
    if not session.get('admin_logged_in'):
        return redirect('/')
    dep_id = request.form.get('id')
    with get_db() as conn:
        dep = conn.execute("SELECT * FROM deposits WHERE id = ?", (dep_id,)).fetchone()
        if dep:
            conn.execute("UPDATE deposits SET status = '✅ Approved' WHERE id = ?", (dep_id,))
            conn.execute("UPDATE users SET inv = round(inv + ?, 2) WHERE uid = ?", (dep['amount'], dep['uid']))
            conn.commit()
            session['flash_msg'] = f"Deposit #{dep_id} approved and ${dep['amount']} added to {dep['uid']} investment!"
    return redirect('/')

@admin_app.route('/reject_deposit', methods=['POST'])
def reject_deposit():
    if not session.get('admin_logged_in'):
        return redirect('/')
    dep_id = request.form.get('id')
    with get_db() as conn:
        conn.execute("UPDATE deposits SET status = '❌ Rejected' WHERE id = ?", (dep_id,))
        conn.commit()
        session['flash_msg'] = f"Deposit #{dep_id} has been rejected."
    return redirect('/')

@admin_app.route('/approve_withdrawal', methods=['POST'])
def approve_withdrawal():
    if not session.get('admin_logged_in'):
        return redirect('/')
    wit_id = request.form.get('id')
    with get_db() as conn:
        conn.execute("UPDATE withdrawals SET status = '✅ Approved' WHERE id = ?", (wit_id,))
        conn.commit()
        session['flash_msg'] = f"Withdrawal #{wit_id} marked as approved."
    return redirect('/')

@admin_app.route('/reject_withdrawal', methods=['POST'])
def reject_withdrawal():
    if not session.get('admin_logged_in'):
        return redirect('/')
    wit_id = request.form.get('id')
    with get_db() as conn:
        wit = conn.execute("SELECT * FROM withdrawals WHERE id = ?", (wit_id,)).fetchone()
        if wit:
            conn.execute("UPDATE withdrawals SET status = '❌ Rejected' WHERE id = ?", (wit_id,))
            conn.execute("UPDATE users SET profit_wallet = round(profit_wallet + ?, 2) WHERE uid = ?", (wit['amount'], wit['uid']))
            conn.commit()
            session['flash_msg'] = f"Withdrawal #{wit_id} rejected and ${wit['amount']} refunded to {wit['uid']} profit wallet."
    return redirect('/')

@admin_app.route('/update_user', methods=['POST'])
def update_user():
    if not session.get('admin_logged_in'):
        return redirect('/')
    uid = request.form.get('uid')
    rank = request.form.get('rank')
    inv = float(request.form.get('inv') or 0.0)
    profit_wallet = float(request.form.get('profit_wallet') or 0.0)
    status = request.form.get('status')
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET rank = ?, inv = ?, profit_wallet = ?, status = ? WHERE uid = ?",
            (rank, inv, profit_wallet, status, uid)
        )
        conn.commit()
        session['flash_msg'] = f"User record for {uid} updated successfully!"
    return redirect('/')

if __name__ == '__main__':
    admin_app.run(host='0.0.0.0', port=50002, debug=False)
