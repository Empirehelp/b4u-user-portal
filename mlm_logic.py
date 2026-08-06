from database import get_db

def get_downline_tree(uid, level=1, visited=None):
    if visited is None:
        visited = set()
    
    if uid in visited or level > 15:
        return []
        
    visited.add(uid)
    tree = []
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT uid, name, rank, inv, status FROM users WHERE referrer = %s", (uid,))
        referrals = cursor.fetchall()
        
        for ref in referrals:
            ref_dict = dict(ref)
            ref_dict['level'] = level
            tree.append(ref_dict)
            tree.extend(get_downline_tree(ref['uid'], level + 1, visited))
            
    except Exception as e:
        print(f"Error fetching downline for {uid}: {e}")
    finally:
        cursor.close()
        conn.close()
        
    return tree

def generate_next_uid():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT uid FROM users ORDER BY uid DESC LIMIT 1")
        last_user = cursor.fetchone()
        if last_user and last_user['uid'].startswith('B4U'):
            num = int(last_user['uid'][3:]) + 1
            return f"B4U{num}"
        return "B4U1001"
    except Exception:
        return "B4U1001"
    finally:
        cursor.close()
        conn.close()

def calculate_team_investment(uid):
    return 0.0

def get_coin_price():
    return 1.0
