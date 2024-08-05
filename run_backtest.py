from datetime import datetime

from model.config import Config

from analysis_tools.compute_data import compute_funding_dataframe
from analysis_tools.loading_data import loading_data
from static_data import START_TIME, END_TIME
from strategy.best_gain import BestGain


def run() -> None:
    from static_data import INVENTORY, INIT_QUANTITY, HAIRCUTS, INITIAL_PRICES


    dataset = loading_data()

    config = Config(
        dataset=dataset,
        start_date=datetime.strptime(START_TIME, "%d-%m-%Y"),
        end_date=datetime.strptime(END_TIME, "%d-%m-%Y"),
    )

    funding_df = compute_funding_dataframe(dataset, INVENTORY, INITIAL_PRICES)

    strat = BestGain(funding_df, config, INVENTORY, INIT_QUANTITY, HAIRCUTS)

    strat.apply()

    strat.apply_stats()



