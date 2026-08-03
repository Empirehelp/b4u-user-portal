import json
import sqlite3
from werkzeug.security import generate_password_hash

data = json.load(open('database.json'))
conn = sqlite3.connect('database.db')

conn.execute('''CREATE TABLE IF NOT EXISTS users (
    uid TEXT PRIMARY KEY, name TEXT, password TEXT, rank TEXT, 
    inv REAL, cash REAL, profit_wallet REAL, status TEXT, 
    referrer TEXT, role TEXT, bonus_claimed INTEGER, bonus_amount REAL, created_at TEXT
)''')

for k, v in data.get('users', {}).items():
    raw_pwd = v['password']
    hashed_pwd = raw_pwd if raw_pwd.startswith('pbkdf2:') else generate_password_hash(raw_pwd)
    conn.execute('''INSERT OR REPLACE INTO users 
        (uid, name, password, rank, inv, cash, profit_wallet, status, referrer, role, bonus_claimed, bonus_amount) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        (k, v['name'], hashed_pwd, v.get('rank', 'Tiffany'), float(v.get('inv', 0)), 
         float(v.get('cash', 0)), float(v.get('profit_wallet', 0)), v.get('status', 'Active'), 
         v.get('referrer'), v.get('role', 'Member'), 1 if v.get('bonus_claimed') else 0, float(v.get('bonus_amount', 0))))

conn.commit()
conn.close()
print("✅ Migration Complete Successfully!")
