from dataclasses import dataclass

import pandas as pd


@dataclass()
class Dataset:
    funding_rates_binance: pd.DataFrame
    funding_rates_bybit: pd.DataFrame
    spot_prices_binance: pd.DataFrame


def loading_data() -> Dataset:
    # Charger les fichiers CSV
    funding_rates_binance = pd.read_csv('./files/Binance_funding.csv', parse_dates=['calc_time'])
    funding_rates_bybit = pd.read_csv('./files/Bybit_funding.csv', parse_dates=['fundingRateTimestamp'])
    spot_prices_binance = pd.read_csv('./files/Binance_hourly.csv', parse_dates=['close_time'])

    spot_prices_binance["open_time"] = pd.to_datetime(spot_prices_binance["open_time"])

    # Renommer les colonnes pour faciliter la manipulation des données
    funding_rates_binance.columns = ['timestamp', 'token', 'funding_interval_hours', 'last_funding_rate']
    funding_rates_bybit.columns = ['timestamp', 'token', 'symbol', 'funding_rate']
    spot_prices_binance.columns = ['close_time', 'token', 'open_time', 'open', 'high', 'low', 'close', 'volume',
                                   'quote_volume', 'count', 'taker_buy_volume', 'taker_buy_quote_volume', 'ignore']

    return Dataset(
        funding_rates_binance=funding_rates_binance,
        funding_rates_bybit=funding_rates_bybit,
        spot_prices_binance=spot_prices_binance,
    )
