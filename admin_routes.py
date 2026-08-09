from flask import Blueprint, request, redirect, render_template_string, session
from database import get_db

admin_bp = Blueprint('admin_bp', __name__)

ADMIN_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ADMIN PANEL - B4U NETWORK</title>
    <style>
        body { background: #0f0518; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 25px; }
        h1 { color: #fdb913; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid rgba(253,185,19,0.3); padding-bottom: 15px; margin-top: 0; }
        .box { background: rgba(35, 13, 56, 0.7); padding: 20px; border-radius: 14px; margin-bottom: 25px; border: 1px solid rgba(74, 37, 109, 0.8); }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #4a256d; font-size: 13px; }
        th { color: #fdb913; background: rgba(74, 37, 109, 0.4); }
        .btn { padding: 6px 12px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 11px; text-decoration: none; }
        .btn-success { background: #10b981; color: white; }
        .btn-danger { background: #ef4444; color: white; }
        .logout-btn { background: #ef4444; color: white; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-size: 12px; }
    </style>
</head>
<body>
    <h1>
        <span>⚙️ ADMIN COMMAND CENTER</span>
        <a href="/logout" class="logout-btn">LOGOUT</a>
    </h1>

    <div class="box">
        <h2>👥 All Users Management</h2>
        <table>
            <tr>
                <th>UID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Investment</th>
                <th>Profit Wallet</th>
                <th>Rank</th>
                <th>Status</th>
            </tr>
            {% for u in users %}
            <tr>
                <td><code>{{ u.uid }}</code></td>
                <td>{{ u.name }}</td>
                <td>{{ u.email }}</td>
                <td>${{ "{:,.2f}".format(u.inv) }}</td>
                <td>${{ "{:,.2f}".format(u.profit_wallet) }}</td>
                <td>{{ u.rank }}</td>
                <td>{{ u.status }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="box">
        <h2>💰 Pending Deposits</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>UID</th>
                <th>Method</th>
                <th>Amount</th>
                <th>Reference</th>
                <th>Action</th>
            </tr>
            {% for d in deposits %}
            <tr>
                <td>{{ d.id }}</td>
                <td><code>{{ d.uid }}</code></td>
                <td>{{ d.method }}</td>
                <td>${{ "{:,.2f}".format(d.amount) }}</td>
                <td>{{ d.address }}</td>
                <td>
                    <form action="/admin/approve_deposit/{{ d.id }}" method="POST" style="display:inline;">
                        <button type="submit" class="btn btn-success">Approve</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@admin_bp.route('/admin')
def admin_panel():
    if 'uid' not in session:
        return redirect('/login')
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        cur.execute("SELECT * FROM deposits WHERE status = 'Pending'")
        deposits = cur.fetchall()
    finally:
        cur.close()
        conn.close()
        
    return render_template_string(ADMIN_HTML, users=users, deposits=deposits)

@admin_bp.route('/admin/approve_deposit/<int:dep_id>', methods=['POST'])
def approve_deposit(dep_id):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM deposits WHERE id = %s", (dep_id,))
        dep = cur.fetchone()
        if dep and dep['status'] == 'Pending':
            cur.execute("UPDATE deposits SET status = 'Approved' WHERE id = %s", (dep_id,))
            cur.execute("UPDATE users SET inv = inv + %s WHERE uid = %s", (dep['amount'], dep['uid']))
            conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    return redirect('/admin')
