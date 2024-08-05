import pandas as pd
import numpy as np


from model.config import Config


class MaxFundingRate:
    """
    This strategy suppose that you have enough amount in an exchange (ie: Binance) to hedge
    your position when you short the perp market

    You will invest on the funding rate with the best ratio, we mean when your funding rate
    is positive you will short the perp market and you will buy the spot on the other exchange,

    Like that you have no exposure on the crypto currency and you will gain only the paid fee.
    otherwise you just keep the amount of crypto
    """

    def __init__(self):
        self.result: pd.DataFrame = None

    def apply(self, df_funding: pd.DataFrame, config: Config):
        result = {}

        last_date = df_funding["timestamp"].unique().tolist()[-1]

        if not config.is_reinvest:
            df_funding["gain_crypto_binance"] = np.where(df_funding["is_buy_long_perp_binance"], 0, df_funding["current_quantity_hold"]*(df_funding["funding_rate_binance"]))
            df_funding["gain_crypto_bybite"] = np.where(df_funding["is_buy_long_perp_bybite"], 0, df_funding["current_quantity_hold"]*(df_funding["funding_rate_bybite"]))
        else:
            raise Exception("This strategy is not implemented with a reinvesment feature")


        for token in df_funding["token"].unique().tolist():
            if token == "USDT":
                continue
            df = df_funding.loc[df_funding["token"]==f"{token}"][["is_funding_binance_best", "gain_crypto_binance", "gain_crypto_bybite"]]
            df["result"] = df.apply(lambda x: x["gain_crypto_binance"] if x["is_funding_binance_best"] else x["gain_crypto_bybite"], axis=1)
            quantity = float(df["result"].sum())
            result[token] = {
                "quantity": float(quantity),
                "amount_usd": float(quantity * config.dataset.spot_prices_binance.loc[(config.dataset.spot_prices_binance["close_time"]==last_date) & (config.dataset.spot_prices_binance["token"]==f"{token}")]["close"].values[0])
            }

        self.result = pd.DataFrame(result)


