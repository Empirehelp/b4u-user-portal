# ==========================================
# RANKS CONFIGURATION (Level 5 Support)
# ==========================================
RANKS_CONFIG = {
"Tiffany": {
"min_p": 10,
"max_p": 699,
"min_t": 0,
"ib": [0.03, 0.02, 0.01, 0.00, 0.00],  # Levels 1 to 5
"pb": [0.03, 0.01, 0.01, 0.00, 0.00],
},
"Blue Moon": {
"min_p": 700,
"max_p": 2999,
"min_t": 5000,
"ib": [0.07, 0.03, 0.01, 0.00, 0.00],
"pb": [0.05, 0.03, 0.01, 0.00, 0.00],
},
"Aurora": {
"min_p": 3000,
"max_p": 9999,
"min_t": 30000,
"ib": [0.10, 0.03, 0.01, 0.01, 0.01],
"pb": [0.07, 0.03, 0.01, 0.01, 0.01],
},
"Cullinan": {
"min_p": 10000,
"max_p": 29999,
"min_t": 100000,
"ib": [0.10, 0.05, 0.03, 0.01, 0.01],
"pb": [0.08, 0.05, 0.03, 0.01, 0.01],
},
"Sancy": {
"min_p": 30000,
"max_p": 49999,
"min_t": 500000,
"ib": [0.12, 0.05, 0.03, 0.03, 0.03],
"pb": [0.10, 0.05, 0.03, 0.03, 0.03],
},
"KohiNoor": {
"min_p": 50000,
"max_p": 1000000,
"min_t": 1000000,
"ib": [0.15, 0.07, 0.03, 0.03, 0.03],
"pb": [0.12, 0.05, 0.03, 0.03, 0.03],
},
}


# ==========================================
# CORE USER & LOGIC FUNCTIONS
# ==========================================

def get_user_rank(personal_points: float, team_points: float) -> str:
    """
    User ke personal points aur team turnover ke mutabiq uska rank determine karta hai.
    """
    ranks_hierarchy = [
        "KohiNoor",
        "Sancy",
        "Cullinan",
        "Aurora",
        "Blue Moon",
        "Tiffany"
    ]

    for rank_name in ranks_hierarchy:
        config = RANKS_CONFIG[rank_name]
        if (config["min_p"] <= personal_points <= config["max_p"] and
            team_points >= config["min_t"]):
            return rank_name

    return "Tiffany"


def calculate_level_bonuses(user_rank: str, level: int, investment_amount: float) -> dict:
    """
    Level 1 se lekar Level 5 tak ke Investment Bonus (IB) aur Pool Bonus (PB) calculate karta hai.
    """
    if not (1 <= level <= 5):
        return {
            "error": "Level must be between 1 and 5",
            "ib_rate": 0.0, "pb_rate": 0.0,
            "ib_amount": 0.0, "pb_amount": 0.0
        }

    idx = level - 1
    config = RANKS_CONFIG.get(user_rank, RANKS_CONFIG["Tiffany"])

    ib_rate = config["ib"][idx]
    pb_rate = config["pb"][idx]

    return {
        "rank": user_rank,
        "level": level,
        "ib_rate": ib_rate,
        "pb_rate": pb_rate,
        "ib_amount": investment_amount * ib_rate,
        "pb_amount": investment_amount * pb_rate
    }


def process_user_rewards(user_data: dict, downline_investments: dict) -> dict:
    """
    User side par poori profile process karne ke liye function.
    """
    p_points = user_data.get("personal_points", 0.0)
    t_points = user_data.get("team_points", 0.0)

    user_rank = get_user_rank(p_points, t_points)

    total_ib = 0.0
    total_pb = 0.0
    breakdown = {}

    for lvl in range(1, 6):
        inv_amount = downline_investments.get(lvl, 0.0)
        res = calculate_level_bonuses(user_rank, lvl, inv_amount)

        total_ib += res["ib_amount"]
        total_pb += res["pb_amount"]
        breakdown[f"Level_{lvl}"] = res

    return {
        "username": user_data.get("username", "Unknown"),
        "current_rank": user_rank,
        "total_investment_bonus": total_ib,
        "total_pool_bonus": total_pb,
        "level_breakdown": breakdown
    }


# ==========================================
# DATABASE & HELPER FUNCTIONS
# ==========================================

def generate_next_uid() -> str:
    """
    Naye user ke liye unique ID generate karta hai.
    """
    import random
    return f"UID{random.randint(100000, 999999)}"


def calculate_team_investment(downline_input) -> float:
    """
    Team ki total investment calculate karta hai.
    """
    total = 0.0
    if not downline_input:
        return total

    if isinstance(downline_input, str):
        try:
            from app import supabase
            res = supabase.table("users").select("inv").eq("referrer", downline_input).execute()
            if res.data:
                for row in res.data:
                    total += float(row.get("inv", 0.0) or 0.0)
        except Exception:
            pass
        return total

    if isinstance(downline_input, list):
        for user in downline_input:
            if isinstance(user, dict):
                total += float(user.get("inv", user.get("investment", 0.0)) or 0.0)
            elif isinstance(user, (int, float)):
                total += float(user)
    elif isinstance(downline_input, dict):
        total += float(downline_input.get("inv", downline_input.get("investment", 0.0)) or 0.0)

    return total


def calculate_team_investment_by_levels(downline_by_level) -> dict:
    """
    Level-wise downline investment calculate karta hai.
    """
    level_totals = {}
    if not downline_by_level:
        return level_totals

    if isinstance(downline_by_level, dict):
        for level, users in downline_by_level.items():
            level_totals[level] = calculate_team_investment(users)

    return level_totals


def get_downline_tree(user_id: str, all_users_db: list = None) -> dict:
    """
    User ki downline tree structure return karta hai (Level 1 se 5 tak).
    """
    levels_dict = {1: [], 2: [], 3: [], 4: [], 5: []}
    try:
        from app import supabase
        l1_res = supabase.table("users").select("*").eq("referrer", user_id).execute()
        l1_users = l1_res.data if l1_res and l1_res.data else []
        levels_dict[1] = l1_users

        l1_uids = [u.get("uid") for u in l1_users if u.get("uid")]
        if l1_uids:
            l2_res = supabase.table("users").select("*").in_("referrer", l1_uids).execute()
            l2_users = l2_res.data if l2_res and l2_res.data else []
            levels_dict[2] = l2_users

        l2_uids = [u.get("uid") for u in l2_users if u.get("uid")]
        if l2_uids:
            l3_res = supabase.table("users").select("*").in_("referrer", l2_uids).execute()
            l3_users = l3_res.data if l3_res and l3_res.data else []
            levels_dict[3] = l3_users

        l3_uids = [u.get("uid") for u in l3_users if u.get("uid")]
        if l3_uids:
            l4_res = supabase.table("users").select("*").in_("referrer", l3_uids).execute()
            l4_users = l4_res.data if l4_res and l4_res.data else []
            levels_dict[4] = l4_users

        l4_uids = [u.get("uid") for u in l4_users if u.get("uid")]
        if l4_uids:
            l5_res = supabase.table("users").select("*").in_("referrer", l4_uids).execute()
            l5_users = l5_res.data if l5_res and l5_res.data else []
            levels_dict[5] = l5_users
    except Exception:
        pass

    return {
        "user_id": user_id,
        "levels": levels_dict
    }


def get_coin_price():
    """
    Current platform coin price aur related market data return karta hai.
    """
    coin_price = 1.05
    coin_change = 2.5
    total_inv = 10000.0
    btc_usd = 65000.0
    b4u_in_btc = 0.000015
    
    return coin_price, coin_change, total_inv, btc_usd, b4u_in_btc
