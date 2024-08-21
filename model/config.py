from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict

from analysis_tools.loading_data import Dataset


@dataclass()
class Config:
    dataset: Dataset
    start_date: datetime
    end_date: datetime
    buffer_liquidation: float = 0.1 # 0.05 5% to prevent liquidation
    required_collateral: float = 0.3 # 30% to prevent liquidation
    spot_perp_fee: float = 0.00005 # 0.05% to prevent liquidation
    taker_fee: float = 0.0001 # 0.1% to prevent liquidation
    spot_fee: float = 0.000055 # 0.055% to prevent liquidation
    tokens: List[str] = field(default_factory=list)
    is_reinvest: bool = False # for max funding rate

    # Initial prices for each token

