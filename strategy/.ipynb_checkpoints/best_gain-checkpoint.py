import pandas as pd
from model.config import Config
from static_data import HAIRCUTS, INIT_QUANTITY


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

    def __init__(self, funding_df: pd.DataFrame, config: Config):
        self.config = config
        # Extract spot price data from the config
        self.df_spot_perp = config.dataset.spot_prices_binance[["close_time", "close", "token"]]
        # Merge funding data with spot price data
        self.df = self._merge_data(funding_df)
        # Placeholder for the final result
        self.result = None

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
            self.collateral_needed = 0
            # Filter rows for the current date
            df_date = self.df[self.df.timestamp == date].copy()
            self._calculate_collateral_values(df_date)
            df_date["potential_gain"] = df_date.apply(self._apply_potential_gain, axis=1)
            df_date["potential_gain_usd"] = df_date["potential_gain"] * df_date["close"]
            df_date["collateral_needed_usd"] = df_date["current_quantity_hold"] * df_date["close"]
            # Sort by potential gain in USD
            sorted_df = df_date.sort_values(by=['potential_gain_usd'])
            # Sum up the total collateral needed for the day
            self.collateral_needed = sorted_df["collateral_needed_usd"].sum()
            # Determine the action (POSTED or INVESTED) based on collateral needs
            sorted_df["ACTION"] = sorted_df.apply(self._apply_best_allocation, axis=1)
            sorted_df["is_usdt_invest"] = False
            # USDT line management
            over_collateralised_available = (self.collateral_posted - self.collateral_needed) * (1-self.config.buffer_liquidation)
            last_row_copy = sorted_df.iloc[-1].copy()
            last_row_copy["token"] = "USDT"
            last_row_copy["collateral_needed_usd"] = INIT_QUANTITY["USDT"] if over_collateralised_available > INIT_QUANTITY["USDT"] else over_collateralised_available
            last_row_copy["collateral_value_usd"] = last_row_copy["collateral_needed_usd"] / self.config.required_collateral
            last_row_copy["potential_gain"] = self._apply_potential_gain_usdt(last_row_copy)
            last_row_copy["potential_gain_usd"] = last_row_copy["potential_gain"] * last_row_copy["close"]
            last_row_copy["is_usdt_invest"] = True
            # Append the modified row to the DataFrame using pd.concat
            sorted_df = pd.concat([sorted_df, last_row_copy.to_frame().T], ignore_index=True)
            df_list.append(sorted_df)
        # Concatenate all the processed daily data
        self.result = pd.concat(df_list)
        # Format the timestamp into a readable date format
        self.result["date_daily"] = pd.to_datetime(self.result["timestamp"]).dt.strftime("%d-%m-%Y")

    def _calculate_collateral_values(self, df: pd.DataFrame):
        # Calculate collateral value adjusted by the haircut value
        df["collateral_value"] = df.apply(
            lambda x: x["current_quantity_hold"] * HAIRCUTS.get(x["token"][:-4], 1), axis=1
        )
        # Convert collateral value to USD equivalent
        df["collateral_value_usd"] = (df["collateral_value"] * df["close"]) / self.config.required_collateral

    @staticmethod
    def _apply_potential_gain(row):
        # Calculate potential gain based on funding rates
        if row["funding_rate_binance"] <= 0 and row["funding_rate_bybite"] <= 0:
            return 0
        return row['current_quantity_hold'] * max(row["funding_rate_binance"], row["funding_rate_bybite"])

    @staticmethod
    def _apply_potential_gain_usdt(row):
        return (row['collateral_needed_usd'] / row['close']) * max(row["funding_rate_binance"], row["funding_rate_bybite"])

    def _apply_best_allocation(self, row):
        # Allocate collateral based on whether the total needed collateral has been posted
        if self.collateral_needed > self.collateral_posted:
            self.collateral_needed -= row["collateral_needed_usd"]
            self.collateral_posted += row["collateral_value_usd"]
            return "POSTED"
        return "INVESTED"