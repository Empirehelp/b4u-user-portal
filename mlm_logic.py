import requests

def get_coin_price(coin_id="bitcoin"):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data.get(coin_id, {}).get('usd', 0.0)
    except Exception:
        return 0.0
