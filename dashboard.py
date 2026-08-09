from flask import Blueprint, request, redirect, render_template_string, session, url_for
from database import get_db
from mlm_logic import get_coin_price, get_downline_tree

dash_bp = Blueprint('dash_bp', __name__)

DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>USER DASHBOARD - B4U NETWORK</title>
    <style>
        body { background: #0f0518; color: #e9ecef; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 25px; }
        h1 { color: #fdb913; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid rgba(253,185,19,0.3); padding-bottom: 15px; margin-top: 0; font-size: 1.5rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-bottom: 25px; }
        .stat-card { background: rgba(35, 13, 56, 0.8); border: 1px solid rgba(74, 37, 109, 0.8); border-radius: 12px; padding: 20px; text-align: center; border-top: 4px solid #fdb913; }
        .stat-num { font-size: 24px; font-weight: bold; color: white; margin-top: 8px; }
        h2 { color: #a78bfa; margin-top: 30px; border-bottom: 1px solid rgba(74, 37, 109, 0.8); padding-bottom: 8px; font-size: 16px; }
        .box { background: rgba(35, 13, 56, 0.7); padding: 20px; border-radius: 14px; margin-bottom: 25px; border: 1px solid rgba(74, 37, 109, 0.8); }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 13px; text-decoration: none; display: inline-block; }
        .btn-success { background: #10b981; color: white; }
        .logout-btn { background: #ef4444; color: white; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: bold; }
        input, select { width: 100%; padding: 12px; background: #130620; border: 1px solid #4a256d; border-radius: 8px; color: white; margin-bottom: 12px; box-sizing: border-box; outline: none; }
        input:focus { border-color: #fdb913; }
        .msg-alert { padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; font-weight: bold; text-align: center; background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); }
        code { background: #190828; padding: 4px 8px; border-radius: 6px; color: #fdb913; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #4a256d; font-size: 12px; }
        th { color: #fdb913; background: rgba(74, 37, 109, 0.4); }
        .crypto-ticker { display: flex; gap: 15px; overflow-x: auto; margin-bottom: 20px; }
        .crypto-badge { background: rgba(35, 13, 56, 0.9); border: 1px solid #4a256d; padding: 10px 15px; border-radius: 8px; font-size: 13px; font-weight: bold; color: #fdb913; white-space: nowrap; }
    </style>
</head>
<body>
    <h1>
        <span>💎 WELCOME, {{ user.name }} (UID: <code>{{ user.uid }}</code>)</span>
        <a href="/logout" class="logout-btn">LOGOUT</a>
    </h1>

    {% if msg %}
    <div class="msg-alert">{{ msg }}</div>
    {% endif %}

    <!-- Live Crypto Ticker -->
    <div class="crypto-ticker">
        <div class="crypto-badge">Bitcoin (BTC): ${{ btc_price }}</div>
        <div class="crypto-badge">Ethereum (ETH): ${{ eth_price }}</div>
        <div class="crypto-badge">B4U Coin: $1.25</div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <small style="color:#a78bfa; font-weight:bold;">ACTIVE INVESTMENT</small>
            <div class="stat-num" style="color:#10b981;">${{ "{:,.2f}".format(user.inv) }}</div>
        </div>
        <div class="stat-card" style="border-top-color: #10b981;">
            <small style="color:#a78bfa; font-weight:bold;">PROFIT WALLET</small>
            <div class="stat-num" style="color:#fdb913;">${{ "{:,.2f}".format(user.profit_wallet) }}</div>
        </div>
        <div class="stat-card" style="border-top-color: #3b82f6;">
            <small style="color:#a78bfa; font-weight:bold;">ACCOUNT RANK</small>
            <div class="stat-num" style="color:#60a5fa;">{{ user.rank }}</div>
        </div>
        <div class="stat-card" style="border-top-color: #ef4444;">
            <small style="color:#a78bfa; font-weight:bold;">STATUS</small>
            <div class="stat-num" style="color: {% if user.status == 'Active' %}#10b981{% else %}#ef4444{% endif %};">{{ user.status }}</div>
        </div>
    </div>

    <div class="box">
        <h2>🔗 Referral Link & Network</h2>
        <p>Invite others using your unique referral link:</p>
        <input type="text" readonly value="{{ request.host_url }}register?ref={{ user.uid }}" onclick="this.select();">
        <p style="margin-top:10px;">Sponsor UID: <code>{{ user.sponsor_uid }}</code></p>
    </div>

    <!-- P2P Wallet Transfer -->
    <div class="box">
        <h2>🔄 P2P Wallet Transfer</h2>
        <form action="/p2p_transfer" method="POST">
            <input type="text" name="recipient_uid" placeholder="Recipient UID (e.g. B4U1002)" required>
            <input type="number" step="0.01" name="amount" placeholder="Transfer Amount ($)" required>
            <button type="submit" class="btn btn-success" style="background:#8b5cf6;">Send P2P Transfer</button>
        </form>
    </div>

    <!-- Level 5 Downline Tree -->
    <div class="box">
        <h2>🌳 Level 1 to Level 5 Downline Tree</h2>
        {% for level, members in tree.items() %}
            <h3 style="color:#fdb913; font-size:14px; margin-top:15px;">Level {{ level }} (Total: {{ members|length }})</h3>
            {% if members %}
            <table>
                <tr>
                    <th>UID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Investment</th>
                    <th>Rank</th>
                    <th>Status</th>
                </tr>
                {% for m in members %}
                <tr>
                    <td><code>{{ m.uid }}</code></td>
                    <td>{{ m.name }}</td>
                    <td>{{ m.email }}</td>
                    <td>${{ "{:,.2f}".format(m.inv) }}</td>
                    <td>{{ m.rank }}</td>
                    <td>{{ m.status }}</td>
                </tr>
                {% endfor %}
            </table>
            {% else %}
            <p style="font-size:12px; color:#a78bfa; margin:5px 0;">No members in Level {{ level }} yet.</p>
            {% endif %}
        {% endfor %}
    </div>

    <div class="box">
        <h2>💰 Deposit Funds</h2>
        <form action="/deposit" method="POST">
            <select name="method">
                <option value="USDT (TRC20)">USDT (TRC20)</option>
                <option value="Bitcoin">Bitcoin (BTC)</option>
                <option value="Ethereum">Ethereum (ETH)</option>
                <option value="B4U Coin">B4U Coin</option>
            </select>
            <input type="number" step="0.01" name="amount" placeholder="Enter Deposit Amount ($)" required>
            <input type="text" name="address" placeholder="Transaction Hash / Reference ID" required>
            <button type="submit" class="btn btn-success">Submit Deposit Request</button>
        </form>
    </div>

    <div class="box">
        <h2>💸 Request Withdrawal</h2>
        <form action="/withdraw" method="POST">
            <select name="method">
                <option value="USDT (TRC20)">USDT (TRC20)</option>
                <option value="Bank Wire">Bank Wire</option>
            </select>
            <input type="number" step="0.01" name="amount" placeholder="Withdrawal Amount ($)" required>
            <input type="text" name="address" placeholder="Your Destination Wallet / Account Details" required>
            <button type="submit" class="btn btn-success" style="background:#3b82f6;">Submit Withdrawal Request</button>
        </form>
    </div>
</body>
</html>
"""

@dash_bp.route('/dashboard')
def dashboard():
    if 'uid' not in session:
        return redirect(url_for('auth_bp.login'))
    
    uid = session['uid']
    msg = request.args.get('msg', None)
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM users WHERE uid = %s", (uid,))
        user = cur.fetchone()
        
        # Fetch downline tree
        tree = get_downline_tree(cur, uid)
    finally:
        cur.close()
        conn.close()
        
    if not user:
        return redirect(url_for('auth_bp.logout'))
        
    btc_price = get_coin_price("bitcoin")
    eth_price = get_coin_price("ethereum")
        
    return render_template_string(DASHBOARD_HTML, user=user, tree=tree, btc_price=btc_price, eth_price=eth_price, msg=msg)

@dash_bp.route('/p2p_transfer', methods=['POST'])
def p2p_transfer():
    if 'uid' not in session:
        return redirect(url_for('auth_bp.login'))
    
    sender_uid = session['uid']
    recipient_uid = request.form.get('recipient_uid').strip()
    try:
        amount = float(request.form.get('amount'))
    except:
        return redirect(url_for('dash_bp.dashboard', msg="Invalid amount!"))
        
    if amount <= 0:
        return redirect(url_for('dash_bp.dashboard', msg="Amount must be greater than zero!"))
        
    conn = get_db()
    cur = conn.cursor()
    try:
        # Check sender balance
        cur.execute("SELECT profit_wallet FROM users WHERE uid = %s", (sender_uid,))
        sender = cur.fetchone()
        
        # Check recipient existence
        cur.execute("SELECT uid FROM users WHERE uid = %s", (recipient_uid,))
        recipient = cur.fetchone()
        
        if not recipient:
            msg = "Recipient UID not found!"
        elif sender_uid == recipient_uid:
            msg = "You cannot transfer to yourself!"
        elif float(sender['profit_wallet']) < amount:
            msg = "Insufficient balance in Profit Wallet!"
        else:
            # Execute transfer
            cur.execute("UPDATE users SET profit_wallet = profit_wallet - %s WHERE uid = %s", (amount, sender_uid))
            cur.execute("UPDATE users SET profit_wallet = profit_wallet + %s WHERE uid = %s", (amount, recipient_uid))
            conn.commit()
            msg = f"Successfully transferred ${amount} to {recipient_uid}!"
    except Exception as e:
        conn.rollback()
        msg = f"Transfer error: {str(e)}"
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('dash_bp.dashboard', msg=msg))

@dash_bp.route('/deposit', methods=['POST'])
def deposit():
    if 'uid' not in session:
        return redirect(url_for('auth_bp.login'))
    
    uid = session['uid']
    method = request.form.get('method')
    amount = request.form.get('amount')
    address = request.form.get('address')
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO deposits (uid, method, amount, address, status) VALUES (%s, %s, %s, %s, 'Pending')", 
                    (uid, method, amount, address))
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('dash_bp.dashboard', msg="Deposit request submitted successfully!"))

@dash_bp.route('/withdraw', methods=['POST'])
def withdraw():
    if 'uid' not in session:
        return redirect(url_for('auth_bp.login'))
    
    uid = session['uid']
    method = request.form.get('method')
    amount = float(request.form.get('amount'))
    address = request.form.get('address')
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT profit_wallet FROM users WHERE uid = %s", (uid,))
        user = cur.fetchone()
        if user and float(user['profit_wallet']) >= amount:
            cur.execute("UPDATE users SET profit_wallet = profit_wallet - %s WHERE uid = %s", (amount, uid))
            cur.execute("INSERT INTO withdrawals (uid, method, amount, address, status) VALUES (%s, %s, %s, %s, 'Pending')", 
                        (uid, method, amount, address))
            conn.commit()
            msg = "Withdrawal request submitted successfully!"
        else:
            msg = "Insufficient funds in profit wallet for withdrawal!"
    except Exception as e:
        conn.rollback()
        msg = f"Withdrawal error: {str(e)}"
    finally:
        cur.close()
        conn.close()
        
    return redirect(url_for('dash_bp.dashboard', msg=msg))
