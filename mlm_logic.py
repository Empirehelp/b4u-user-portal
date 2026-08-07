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
    User ke personal points aur team turnover (team points) ke 
    mutabiq uska rank determine karta hai. Top ranks se check 
    karna shuru karta hai taake baray users foran catch ho jayein.
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
            
    # Default fallback agar criteria match na ho
    return "Tiffany"


def calculate_level_bonuses(user_rank: str, level: int, investment_amount: float) -> dict:
    """
    Level 1 se lekar Level 5 tak ke Investment Bonus (IB) aur 
    Pool Bonus (PB) calculate karta hai.
    """
    if not (1 <= level <= 5):
        return {
            "error": "Level must be between 1 and 5",
            "ib_rate": 0.0, "pb_rate": 0.0, 
            "ib_amount": 0.0, "pb_amount": 0.0
        }

    # Python mein lists 0-based index hoti hain (Level 1 index 0 par hai)
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
    downline_investments ek dictionary ho sakti hai jismein 
    {1: amount, 2: amount, ... 5: amount} level-wise investments hon.
    """
    p_points = user_data.get("personal_points", 0.0)
    t_points = user_data.get("team_points", 0.0)
    
    # 1. Rank Find Karein
    user_rank = get_user_rank(p_points, t_points)
    
    # 2. Har level ka bonus calculate karein (Level 1 to 5)
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
