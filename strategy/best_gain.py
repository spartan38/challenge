import pandas as pd
from model.config import Config
import numpy as np

class BestGain:
    """
    Strategy Explanation:
    This strategy involves allocating collateral to tokens where the funding rate is the lowest,
    while simultaneously shorting the token in the perpetual market if the funding rate is positive.
    The goal is to post collateral in the credit line to buy the spot token,
    making the position risk-neutral.
    This way, you earn the funding rate on the short position without any net exposure to the token.

    Important: We keep 5% of overcollateralization to avoid liquidation
    """

    def __init__(self, funding_df: pd.DataFrame, config: Config, inventory, init_quantity, haircuts):
        self.config = config
        # Extract spot price data from the config
        self.df_spot_perp = config.dataset.spot_prices_binance[["close_time", "close", "token"]]
        # Merge funding data with spot price data
        self.df = self._merge_data(funding_df)
        # Placeholder for the final result
        self.result = None
        self.recap = None
        self.inventory = inventory
        self.init_quantity = init_quantity
        self.haircuts = haircuts

    def _merge_data(self, funding_df: pd.DataFrame) -> pd.DataFrame:
        # Perform a merge on the funding data with spot prices on timestamp and token
        merged_df = funding_df.merge(
            self.df_spot_perp, left_on=["timestamp", "token"], right_on=["close_time", "token"]
        ).drop(
            ["funding_interval_hours", "symbol", "is_market_funding_arb", "is_buy_long_perp_binance", "is_buy_long_perp_bybite"], axis=1
        )
        return merged_df

    def apply(self):
        df_list = []
        unique_dates = self.df.timestamp.unique()
        # Process each unique date separately
        for date in unique_dates:
            self.collateral_posted = 0
            # Filter rows for the current date
            df_date = self.df[self.df.timestamp == date].copy()
            self._calculate_collateral_values(df_date)
            self._calculate_gain(df_date)
            # Sort by potential gain in USD
            sorted_df = df_date.sort_values(by=['potential_gain_usd'], ascending=False)

            # USDT line management
            sorted_df["is_usdt_invest"] = False

            last_row_copy = self._compute_last_row(sorted_df)
            # Append the modified row to the DataFrame using pd.concat
            sorted_df = pd.concat([last_row_copy.to_frame().T, sorted_df], ignore_index=True)
            # Sum up the total collateral needed for the day
            self.collateral_available = sorted_df.loc[sorted_df["token"].isin(list(self.inventory.keys())), "collateral_value_usd"].sum()
            self.invested_amount = 0

            self._compute_strategy(sorted_df)

            df_list.append(sorted_df)
        # Concatenate all the processed daily data
        self.result = pd.concat(df_list)
        self.result = self.result.loc[self.result["token"].isin((self.inventory.keys()))]
        # Format the timestamp into a readable date format
        self.result["date_daily"] = pd.to_datetime(self.result["timestamp"]).dt.strftime("%d-%m-%Y")

    def _compute_last_row(self, sorted_df):
        last_row_copy = sorted_df.iloc[0].copy()
        last_row_copy["token"] = "USDT"
        last_row_copy["collateral_needed_usd"] = self.init_quantity["USDT"]
        last_row_copy["collateral_value_usd"] = last_row_copy["collateral_needed_usd"]
        last_row_copy["current_quantity_hold"] = self.init_quantity["USDT"] / last_row_copy["close"]
        last_row_copy["potential_gain"] = self.init_quantity["USDT"] / last_row_copy["close"]
        last_row_copy["potential_gain_usd"] = self._apply_potential_gain(last_row_copy) * last_row_copy["close"]
        last_row_copy["is_usdt_invest"] = True
        return last_row_copy

    def _calculate_gain(self, df):
        df["potential_gain"] = df.apply(self._apply_potential_gain, axis=1)
        df["potential_gain_usd"] = df["potential_gain"] * df["close"]
        df["collateral_needed_usd"] = df["current_quantity_hold"] * df["close"]

    def _compute_strategy(self, df):
        # Determine the action (POSTED or INVESTED) based on collateral needs
        df["ACTION"] = df.apply(self._apply_best_allocation, axis=1)
        # Execute strategy if the fee is lower than the expected return
        is_profitable, fee_amount = self.is_profitable_trade(df)
        df["is_profitable"] = is_profitable
        df["fee_amount"] = fee_amount


    def _calculate_collateral_values(self, df: pd.DataFrame):
        # Calculate collateral value adjusted by the haircut value
        df["collateral_value"] = df.apply(
            lambda x: x["current_quantity_hold"] * self.haircuts.get(x["token"][:-4] if x["token"] in self.inventory.keys() else 0, 1), axis=1
        )
        # Convert collateral value to USD equivalent
        df["collateral_value_usd"] = (df["collateral_value"] * df["close"]) / self.config.required_collateral

    def is_profitable_trade(self, df: pd.DataFrame):
        gain_usd = df.loc[df["ACTION"]=="INVESTED", "potential_gain_usd"].sum()
        fees_amount_spot = 2 * (df.loc[df["ACTION"]=="POSTED", "collateral_value_usd"].sum() * self.config.spot_fee)
        fees_amount_taker = df.loc[df["ACTION"]=="INVESTED", "potential_gain_usd"].sum() * self.config.taker_fee
        fees_amount_spot_perp = 2 * (df.loc[df["ACTION"]=="INVESTED", "collateral_needed_usd"].sum() * self.config.spot_perp_fee)
        fees_amount = (fees_amount_spot + fees_amount_taker + fees_amount_spot_perp)
        return (gain_usd > fees_amount, fees_amount)

    def get_pnl_by_token(self) -> pd.DataFrame:
        profitable_value = self.get_profitable_trade()
        pnl_by_token = profitable_value.pivot_table(values="potential_gain_usd", index="token", columns=[],
                                                    aggfunc='sum')
        pnl_by_token.reset_index(inplace=True)
        pnl_by_token["amount_invested"] = pnl_by_token["token"].apply(lambda x: self.inventory[x])
        pnl_by_token["APY_BY_TOKEN"] = pnl_by_token["potential_gain_usd"] / pnl_by_token["amount_invested"]
        return pnl_by_token

    def get_profitable_trade(self):
        return self.result.loc[(self.result["is_profitable"] == True) & (self.result["ACTION"] == "INVESTED")]

    def apply_stats(self):
        profitable_value = self.get_profitable_trade()
        pnl_by_token = self.get_pnl_by_token()

        fee = profitable_value.pivot_table(values="fee_amount", index="timestamp", columns=[], aggfunc=np.mean).sum().values[0]

        pnl_without_fee = pnl_by_token["potential_gain_usd"].sum()

        pnl = pnl_without_fee - fee
        apy = round(pnl / pnl_by_token["amount_invested"].sum(), 4) * 100

        pnl_by_token["gain_with_fee"] = (pnl / pnl_without_fee) * (pnl_by_token["potential_gain_usd"])
        pnl_by_token["APY_with_fee"] = pnl_by_token["gain_with_fee"] / pnl_by_token["amount_invested"]

        print(f"PnL (with fees) {pnl:.2f} $\n"
              f"           Fees {fee:.2f} $\n"
              f"            APY {apy:.2f} %\n\n"
              f"{'*' * 25} RECAP {'*' * 28}\n\n"
              f"{pnl_by_token}"
              )

        self.recap = {
            "pnl_with_fee":pnl,
            "apy_with_fee":apy,
            "fee_amount":fee,
            "pnl_by_token":pnl_by_token,
        }

    @staticmethod
    def _apply_potential_gain(row):
        # Calculate potential gain based on funding rates
        if row["funding_rate_binance"] <= 0 and row["funding_rate_bybite"] <= 0:
            return 0
        return row['current_quantity_hold'] * max(row["funding_rate_binance"], row["funding_rate_bybite"])

    def _apply_potential_gain_usdt(self, row) -> float:
        available = (self.collateral_posted - self.collateral_needed) * (1 - self.config.buffer_liquidation)
        invest_usdt = self.inventory.get(row["token"]) if available > self.inventory.get(row["token"]) else available
        return (invest_usdt / row['close']) * max(row["funding_rate_binance"], row["funding_rate_bybite"])

    def _apply_best_allocation(self, row) -> str:
        if row["token"] not in list(self.inventory.keys()):
            return ["NOT OWNED"]
        # result = self._compute_best_allocation(row)
        temp = (self.collateral_available - row["collateral_value_usd"]) * (1-self.config.buffer_liquidation)
        # Allocate collateral based on whether the total needed collateral has been posted
        if temp < self.invested_amount + row["collateral_needed_usd"]:
            # todo to optimize to allow a partial allocation
            self.collateral_posted += row["collateral_value_usd"]
            return "POSTED"
        else:
            self.collateral_available -= row["collateral_value_usd"]
            self.invested_amount += row["collateral_needed_usd"]
            return "INVESTED"

    def _compute_best_allocation(self, row):
        pass
