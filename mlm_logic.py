import requests
import re

def get_coin_price(coin_id="bitcoin"):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url, timeout=3)
        data = response.json()
        return data.get(coin_id, {}).get('usd', 0.0)
    except Exception:
        return 0.0

def generate_next_uid(conn):
    """Generates the next unique user ID based on the last registered user."""
    cur = conn.cursor()
    try:
        cur.execute("SELECT uid FROM users ORDER BY id DESC LIMIT 1")
        last_user = cur.fetchone()
        
        if last_user and last_user.get('uid'):
            last_uid = str(last_user['uid'])
            match = re.search(r'\d+', last_uid)
            if match:
                num = int(match.group()) + 1
                prefix = last_uid[:match.start()]
                return f"{prefix}{num}"
        
        return "B4U1001"
    except Exception as e:
        print(f"Error generating UID: {e}")
        return "B4U1001"
    finally:
        cur.close()

def calculate_team_investment(cur, user_uid):
    """Calculates total team investment across the downline tree."""
    try:
        tree = get_downline_tree(cur, user_uid)
        total = 0.0
        for level, users in tree.items():
            for u in users:
                inv = u.get('inv') or 0.0
                try:
                    total += float(inv)
                except ValueError:
                    pass
        return total
    except Exception:
        return 0.0

def get_downline_tree(cur, user_uid):
    tree = {1: [], 2: [], 3: [], 4: [], 5: []}

    cur.execute("SELECT uid, name, email, inv, rank, status, created_at FROM users WHERE sponsor_uid = %s", (user_uid,))
    l1 = cur.fetchall()
    tree[1] = l1

    l1_uids = [u['uid'] for u in l1]
    if l1_uids:
        cur.execute("SELECT uid, name, email, inv, rank, status, created_at FROM users WHERE sponsor_uid = ANY(%s)", (l1_uids,))
        l2 = cur.fetchall()
        tree[2] = l2

        l2_uids = [u['uid'] for u in l2]
        if l2_uids:
            cur.execute("SELECT uid, name, email, inv, rank, status, created_at FROM users WHERE sponsor_uid = ANY(%s)", (l2_uids,))
            l3 = cur.fetchall()
            tree[3] = l3

            l3_uids = [u['uid'] for u in l3]
            if l3_uids:
                cur.execute("SELECT uid, name, email, inv, rank, status, created_at FROM users WHERE sponsor_uid = ANY(%s)", (l3_uids,))
                l4 = cur.fetchall()
                tree[4] = l4

                l4_uids = [u['uid'] for u in l4]
                if l4_uids:
                    cur.execute("SELECT uid, name, email, inv, rank, status, created_at FROM users WHERE sponsor_uid = ANY(%s)", (l4_uids,))
                    l5 = cur.fetchall()
                    tree[5] = l5

    return tree
