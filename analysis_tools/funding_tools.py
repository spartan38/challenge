from static_data import INITIAL_PRICES, HAIRCUTS

import numpy as np
def apply_is_market_funding_arb(row):
    return row["funding_rate_binance"] != row["funding_rate_bybite"]


def apply_is_buy_long_perp_binance(row):
    return row < 0


def apply_is_buy_long_perp_bybite(row):
    return row < 0


def apply_init_quantity(row):
    token = row['token']
    price_current_token = INITIAL_PRICES.get(token)
    return 250_000 / price_current_token

