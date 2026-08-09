import requests

def get_coin_price(coin_id="bitcoin"):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data.get(coin_id, {}).get('usd', 0.0)
    except Exception:
        return 0.0

def get_downline_tree(cur, user_uid):
    """
    Calculates downline members up to 5 Levels deep.
    """
    tree = {1: [], 2: [], 3: [], 4: [], 5: []}
    
    # Level 1
    cur.execute("SELECT uid, name, email, inv, rank, status, created_at FROM users WHERE sponsor_uid = %s", (user_uid,))
    l1 = cur.fetchall()
    tree[1] = l1
    
    # Level 2
    l1_uids = [u['uid'] for u in l1]
    if l1_uids:
        cur.execute("SELECT uid, name, email, inv, rank, status, created_at FROM users WHERE sponsor_uid = ANY(%s)", (l1_uids,))
        l2 = cur.fetchall()
        tree[2] = l2
        
        # Level 3
        l2_uids = [u['uid'] for u in l2]
        if l2_uids:
            cur.execute("SELECT uid, name, email, inv, rank, status, created_at FROM users WHERE sponsor_uid = ANY(%s)", (l2_uids,))
            l3 = cur.fetchall()
            tree[3] = l3
            
            # Level 4
            l3_uids = [u['uid'] for u in l3]
            if l3_uids:
                cur.execute("SELECT uid, name, email, inv, rank, status, created_at FROM users WHERE sponsor_uid = ANY(%s)", (l3_uids,))
                l4 = cur.fetchall()
                tree[4] = l4
                
                # Level 5
                l4_uids = [u['uid'] for u in l4]
                if l4_uids:
                    cur.execute("SELECT uid, name, email, inv, rank, status, created_at FROM users WHERE sponsor_uid = ANY(%s)", (l4_uids,))
                    l5 = cur.fetchall()
                    tree[5] = l5
                    
    return tree
