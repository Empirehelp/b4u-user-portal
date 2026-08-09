# user_routes.py ki line 216 par yeh safe handling code paste kar dein:
res = get_coin_price()
if isinstance(res, tuple) and len(res) == 5:
    coin_price, coin_change, total_inv, btc_usd, b4u_in_btc = res
else:
    coin_price = res if isinstance(res, (int, float)) else 0.0
    coin_change = 0.0
    total_inv = 0.0
    btc_usd = 0.0
    b4u_in_btc = 0.0
