import pandas as pd
import numpy as np


from model.config import Config
from static_data import HAIRCUTS


class MaxFundingRateSec:
    """
    This strategy suppose that you have enough amount in an exchange (ie: Binance) to hedge
    your position when you short the perp market

    You will invest on the funding rate with the best ratio, we mean when your funding rate
    is positive you will short the perp market and you will buy the spot on the other exchange,

    Like that you have no exposure on the crypto currency and you will gain only the paid fee.
    otherwise you just keep the amount of crypto
    """

    def __init__(self, df_funding: pd.DataFrame, config: Config):
        self.result: pd.DataFrame = None
        self.df_funding = df_funding
        self.config = config

    def apply(self):
        result = {}

        spot_perp_price = self.config.dataset.spot_prices_binance

        usdt_gain = []

        gain_crypto = []
        prev_date = None
        current_max_funding = (None, None)

        for i, row in self.df_funding.iterrows():
            if prev_date is None:
                prev_date = row["timestamp"]
                current_max_funding = (row["token"], row["funding_rate_binance"]) if row["funding_rate_binance"] > row["funding_rate_bybite"] else (row["token"], row["funding_rate_bybite"])
            if prev_date != row["timestamp"] and current_max_funding[0] not in [None, ""]:
                # Compute USDT INVESTMENT
                spot_price_t_1 = spot_perp_price.loc[(spot_perp_price["open_time"] == prev_date) & (spot_perp_price["token"] == current_max_funding[0])]["close"].values[0]
                spot_price_t = spot_perp_price.loc[(spot_perp_price["close_time"] == row["timestamp"]) & (spot_perp_price["token"] == current_max_funding[0])]["close"].values[0]
                amount_gained = (((HAIRCUTS.get(current_max_funding[0], 1) * 500_000) / spot_price_t_1) * current_max_funding[1]) * spot_price_t
                usdt_gain.append(amount_gained)
                current_max_funding = ["", 0]


            if any([current_max_funding[1]<row["funding_rate_bybite"], current_max_funding[1]<row["funding_rate_binance"]]):
                current_max_funding = (row["token"], row["funding_rate_binance"]) if row["funding_rate_binance"] > row[
                    "funding_rate_bybite"] else (row["token"], row["funding_rate_bybite"])

            if not self.config.is_reinvest:
                if not row["is_buy_long_perp_binance"] and row["funding_rate_binance"] > row["funding_rate_bybite"]:
                    gain_crypto.append(row["funding_rate_binance"]*row["current_quantity_hold"])
                elif not row["is_buy_long_perp_bybite"] and row["funding_rate_bybite"] > row["funding_rate_binance"]:
                    gain_crypto.append(row["funding_rate_bybite"]*row["current_quantity_hold"])
                else:
                    gain_crypto.append(0)
            else:
                raise Exception("This strategy is not implemented with a reinvesment feature")

        self.df_funding["result"] = gain_crypto

        for token in self.df_funding["token"].unique().tolist():
            if token == "USDT":
                continue
            df = self.df_funding.loc[self.df_funding["token"]==f"{token}"]
            quantity = float(df["result"].sum())
            result[token] = {
                "quantity": float(quantity),
                "amount_usd": float(quantity * self.config.dataset.spot_prices_binance.loc[(self.config.dataset.spot_prices_binance["close_time"]==self.config.end_date) & (self.config.dataset.spot_prices_binance["token"]==f"{token}USDT")]["close"].values[0])
            }
        result["USDUSDT"] = {
            "quantity": sum(usdt_gain),
            "amount_usd": sum(usdt_gain)
        }

        self.result = pd.DataFrame(result)





