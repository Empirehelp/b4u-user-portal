import os
from flask import Flask
from datetime import datetime
from werkzeug.security import generate_password_hash
from database import get_db
from user_routes import user_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'b4u_empire_shadow_sovereign_gate_2026')

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

def init_db():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
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
        );""")
        
        cur.execute("""SELECT column_name FROM information_schema.columns 
                       WHERE table_name='users' AND column_name='p2p_wallet';""")
        if not cur.fetchone():
            cur.execute("ALTER TABLE users ADD COLUMN p2p_wallet REAL DEFAULT 0.0;")

        cur.execute("""CREATE TABLE IF NOT EXISTS deposits (
            id SERIAL PRIMARY KEY,
            uid TEXT,
            amount REAL,
            method TEXT,
            status TEXT DEFAULT '⏳ Pending Verification',
            created_at TEXT
        );""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY,
            uid TEXT,
            amount REAL,
            method TEXT,
            address TEXT,
            status TEXT DEFAULT '⏳ Pending Approval',
            created_at TEXT
        );""")
        
        cur.execute("""CREATE TABLE IF NOT EXISTS p2p_transfers (
            id SERIAL PRIMARY KEY,
            sender TEXT,
            recipient TEXT,
            amount REAL,
            created_at TEXT
        );""")

        cur.execute("SELECT COUNT(*) as count FROM users;")
        user_count = cur.fetchone()['count']
        
        if user_count == 0:
            for uid, name, pwd, rank, inv, profit, p2p_w, status, referrer in SEED_USERS:
                cur.execute(
                    "INSERT INTO users (uid, name, password, rank, inv, profit_wallet, p2p_wallet, status, referrer, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (uid, name, generate_password_hash(pwd), rank, inv, profit, p2p_w, status, referrer, datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
                )
            for uid, amt, method, addr, status in SEED_WITHDRAWALS:
                cur.execute(
                    "INSERT INTO withdrawals (uid, amount, method, address, status, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    (uid, amt, method, addr, status, datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
                )
            cur.execute(
                "INSERT INTO p2p_transfers (sender, recipient, amount, created_at) VALUES (%s, %s, %s, %s)",
                ('B4U1001', 'B4U1003', 100.0, datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
            )
        conn.commit()
    finally:
        cur.close()
        conn.close()

@app.before_request
def setup_db():
    init_db()

app.register_blueprint(user_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50001, debug=False)
