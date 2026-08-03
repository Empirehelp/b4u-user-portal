import json
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_FILE = "database.db"
JSON_FILE = "database.json"

def run_migration():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Tables Creation
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        uid TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        rank TEXT DEFAULT 'Tiffany',
        inv REAL DEFAULT 0.0,
        cash REAL DEFAULT 0.0,
        profit_wallet REAL DEFAULT 0.0,
        status TEXT DEFAULT 'Active',
        referrer TEXT,
        role TEXT DEFAULT 'Member',
        bonus_claimed INTEGER DEFAULT 0,
        bonus_amount REAL DEFAULT 0.0,
        created_at TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT,
        amount REAL,
        method TEXT,
        status TEXT DEFAULT 'Pending'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT,
        amount REAL,
        method TEXT,
        address TEXT,
        status TEXT DEFAULT 'Pending'
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS profit_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        percentage REAL,
        date TEXT,
        message TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS p2p_transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        recipient TEXT,
        amount REAL,
        wallet TEXT
    )''')

    # Load JSON Data
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)

    # 1. Migrate Users
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users = data.get("users", {})
    for uid, u in users.items():
        raw_pwd = u.get("password", "112233")
        hashed_pwd = generate_password_hash(raw_pwd) if not raw_pwd.startswith("pbkdf2:") else raw_pwd

        bonus_claimed = 1 if u.get("bonus_claimed") else 0
        bonus_amount = float(u.get("bonus_amount", 0.0))

        cursor.execute('''INSERT OR REPLACE INTO users 
            (uid, name, password, rank, inv, cash, profit_wallet, status, referrer, role, bonus_claimed, bonus_amount, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (uid, u.get("name"), hashed_pwd, u.get("rank", "Tiffany"),
             float(u.get("inv", 0.0)), float(u.get("cash", 0.0)), float(u.get("profit_wallet", 0.0)),
             u.get("status", "Active"), u.get("referrer"), u.get("role", "Member"),
             bonus_claimed, bonus_amount, now))

    # 2. Migrate Withdrawals
    withdrawals = data.get("withdrawals", [])
    for w in withdrawals:
        cursor.execute('''INSERT OR REPLACE INTO withdrawals (id, uid, amount, method, address, status)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (w.get("id"), w.get("uid"), float(w.get("amount", 0.0)), w.get("method"), w.get("address"), w.get("status")))

    # 3. Migrate Profit History
    profits = data.get("profit_history", [])
    for p in profits:
        cursor.execute('''INSERT INTO profit_history (percentage, date, message) VALUES (?, ?, ?)''',
            (float(p.get("percentage", 0.0)), p.get("date"), f"Distributed {p.get('percentage')}% Profit"))

    # 4. Migrate P2P Transfers
    p2p = data.get("p2p_transfers", [])
    for t in p2p:
        cursor.execute('''INSERT INTO p2p_transfers (sender, recipient, amount, wallet) VALUES (?, ?, ?, ?)''',
            (t.get("sender"), t.get("recipient"), float(t.get("amount", 0.0)), t.get("wallet")))

    conn.commit()
    conn.close()
    print("✅ Migration Complete! All JSON records including P2P transfers are now in database.db")

if __name__ == '__main__':
    run_migration()
