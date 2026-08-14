import requests

def generate_next_uid(cur):
    # Database se sabse bada UID uthayen taake agla sequential mile
    cur.execute("SELECT uid FROM users ORDER BY uid DESC LIMIT 1")
    last_user = cur.fetchone()
    
    if last_user and last_user['uid']:
        last_uid_str = str(last_user['uid'])
        try:
            # "B4U" hata kar number mein 1 add karein
            last_num = int(last_uid_str.replace('B4U', ''))
            new_num = last_num + 1
        except ValueError:
            new_num = 1001
    else:
        # Agar table khali hai, toh 1001 se start karein
        new_num = 1001
        
    return f"B4U{new_num}"

def calculate_team_investment(cur, user_uid):
    cur.execute("SELECT uid FROM users WHERE referrer = %s", (user_uid,))
    downline = cur.fetchall()
    total_volume = 0.0
    for row in downline:
        child_uid = row['uid']
        cur.execute("SELECT inv FROM users WHERE uid = %s", (child_uid,))
        child = cur.fetchone()
        if child:
            total_volume += float(child['inv'] or 0.0)
            total_volume += calculate_team_investment(cur, child_uid)
    return total_volume

def get_downline_tree(cur, user_uid, level=1):
    tree = []
    cur.execute("SELECT uid, name, rank, inv, status FROM users WHERE referrer = %s", (user_uid,))
    downline = cur.fetchall()
    for row in downline:
        tree.append({
            "level": level,
            "uid": row['uid'],
            "name": row['name'],
            "rank": row['rank'],
            "inv": row['inv'],
            "status": row['status']
        })
        tree.extend(get_downline_tree(cur, row['uid'], level + 1))
    return tree

def get_coin_price():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5)
        data = response.json()
        btc_usd = float(data['bitcoin']['usd'])
    except Exception:
        btc_usd = 65000.00

    coin_price = 1.25
    coin_change = 4.5
    total_inv = 154200.00
    b4u_in_btc = round(coin_price / btc_usd, 8) if btc_usd > 0 else 0.000019
    return coin_price, coin_change, total_inv, btc_usd, b4u_in_btc
