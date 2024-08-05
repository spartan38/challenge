from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from analysis_tools.loading_data import Dataset


@dataclass()
class Config:
    dataset: Dataset
    start_date: datetime
    end_date: datetime
    buffer_liquidation: float = 0.05 # 5% to prevent liquidation
    required_collateral: float = 0.3 # 30% to prevent liquidation
    tokens: List[str] = field(default_factory=list)
    is_reinvest: bool = False # for max funding rate