from database import get_db

def generate_next_uid():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT uid FROM users ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if row and row['uid'].startswith("B4U"):
            last_num = int(row['uid'].replace("B4U", ""))
            return f"B4U{last_num + 1}"
        return "B4U1001"
    finally:
        cur.close()
        conn.close()

def calculate_team_investment(uid):
    total = 0.0
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT uid, inv FROM users WHERE referrer = %s", (uid,))
        refs = cur.fetchall()
        for ref in refs:
            total += float(ref['inv'] or 0.0)
            total += calculate_team_investment(ref['uid'])
        return total
    finally:
        cur.close()
        conn.close()

def get_downline_tree(uid, level=1):
    tree = []
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT uid, name, inv, rank, status, created_at FROM users WHERE referrer = %s", (uid,))
        refs = cur.fetchall()
        for ref in refs:
            member = dict(ref)
            member['level'] = level
            tree.append(member)
            tree.extend(get_downline_tree(ref['uid'], level + 1))
        return tree
    finally:
        cur.close()
        conn.close()

def get_coin_price():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT SUM(inv) as total FROM users")
        res = cur.fetchone()
        total_inv = float(res['total'] or 0.0) if res and res['total'] else 0.0
        base_price = 1.00
        price_growth = (total_inv / 1000.0) * 0.05
        coin_price = round(base_price + price_growth, 4)
        coin_change = round(((coin_price - base_price) / base_price) * 100, 2)
        btc_usd = 68500.0
        b4u_in_btc = f"{coin_price / btc_usd:.8f}"
        return coin_price, coin_change, total_inv, btc_usd, b4u_in_btc
    finally:
        cur.close()
        conn.close()
