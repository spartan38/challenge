from typing import Dict

import pandas as pd

from analysis_tools.funding_tools import apply_is_market_funding_arb, apply_is_buy_long_perp_binance, \
    apply_is_buy_long_perp_bybite, apply_init_quantity
from static_data import HAIRCUTS


def compute_collateral_value() -> Dict[str, float]:
    collateral_values = {token: 250000 * hc for token, hc in HAIRCUTS.items()}
    collateral_values['USDT'] = 500000
    return collateral_values

def compute_funding_dataframe(dataset) -> pd.DataFrame:
    funding_df = pd.merge(left=dataset.funding_rates_binance, right=dataset.funding_rates_bybit,
                          on=["timestamp", "token"], how="inner")
    funding_df = funding_df.rename({
        "last_funding_rate": "funding_rate_binance",
        "funding_rate": "funding_rate_bybite",
    }, axis=1)
    funding_df["is_market_funding_arb"] = funding_df.apply(apply_is_market_funding_arb, axis=1)
    funding_df["is_buy_long_perp_binance"] = funding_df["funding_rate_binance"].apply(apply_is_buy_long_perp_binance)
    funding_df["is_buy_long_perp_bybite"] = funding_df["funding_rate_bybite"].apply(apply_is_buy_long_perp_bybite)
    funding_df["is_funding_binance_best"] = funding_df.apply(
        lambda x: x["funding_rate_binance"] > x["funding_rate_bybite"], axis=1)
    funding_df["current_quantity_hold"] = funding_df.apply(apply_init_quantity, axis=1)
    return funding_df