from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class Signal:
    symbol: str
    side: str                # "buy" | "sell" | "none"
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float        # 0.0 – 1.0
    strategy_name: str
    reason: str


class BaseStrategy(ABC):
    """All strategies inherit from this."""

    name: str = "base"
    risk_level: str = "medium"   # low | medium | aggressive

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Signal:
        """Given OHLCV dataframe, return a trade signal."""
        ...

    def _validate_df(self, df: pd.DataFrame) -> None:
        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"DataFrame missing columns: {missing}")
        if len(df) < 50:
            raise ValueError("Need at least 50 candles for reliable signals")
