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
# MISSING FUNCTIONS REQUIRED BY user_routes.py
# ==========================================

def generate_next_uid() -> str:
    """
    Naye user ke liye unique ID generate karta hai.
    """
    import random
    return f"UID{random.randint(100000, 999999)}"


def calculate_team_investment(downline_users: list) -> float:
    """
    Poori downline ki total investment calculate karta hai.
    """
    total = 0.0
    for user in downline_users:
        total += float(user.get("investment", 0.0))
    return total


def calculate_team_investment_by_levels(downline_by_level: dict) -> dict:
    """
    Level-wise downline investment calculate karta hai.
    """
    level_totals = {}
    for level, users in downline_by_level.items():
        level_totals[level] = sum(float(u.get("investment", 0.0)) for u in users)
    return level_totals


def get_downline_tree(user_id: str, all_users_db: list) -> dict:
    """
    User ki downline tree structure return karta hai (levels ke hisaab se).
    """
    # Simple representation ya placeholder agar DB query alag ho
    return {
        "user_id": user_id,
        "levels": {1: [], 2: [], 3: [], 4: [], 5: []}
    }


def get_coin_price() -> float:
    """
    Current platform coin price return karta hai.
    """
    # Default coin price ya live calculation logic
    return 1.00
