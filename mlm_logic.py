from database import get_db

def get_downline_tree(uid, level=1, visited=None):
    if visited is None:
        visited = set()
    
    # Infinite loop aur deep nesting se bachne ke liye guard condition
    if uid in visited or level > 15:
        return []
        
    visited.add(uid)
    tree = []
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Database se is user ke direct referrals fetch karein
        cursor.execute("SELECT uid, name, rank, inv, status FROM users WHERE referrer = %s", (uid,))
        referrals = cursor.fetchall()
        
        for ref in referrals:
            ref_dict = dict(ref)
            ref_dict['level'] = level
            tree.append(ref_dict)
            
            # Aglay level ke liye recursive call (passing the visited set)
            tree.extend(get_downline_tree(ref['uid'], level + 1, visited))
            
    except Exception as e:
        print(f"Error fetching downline for {uid}: {e}")
    finally:
        cursor.close()
        conn.close()  # Connection ko band karna lazmi hai taake leak na ho
        
    return tree
