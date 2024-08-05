def apply_is_market_funding_arb(row):
    return row["funding_rate_binance"] != row["funding_rate_bybite"]


def apply_is_buy_long_perp_binance(row):
    return row < 0


def apply_is_buy_long_perp_bybite(row):
    return row < 0


def apply_init_quantity(row, inventory, initial_prices):
    token = row['token']
    price_current_token = initial_prices.get(token)
    if token not in (inventory.keys()):
        return inventory.get("USDT") / price_current_token
    else:
        price_current_token = initial_prices.get(token)
        return inventory.get(token) / price_current_token

