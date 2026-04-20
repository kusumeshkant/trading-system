from typing import List
import pandas as pd
from app.strategies.base.strategy import BaseStrategy, Signal
from app.core.logger import logger


class SignalEngine:
    """Runs all registered strategies and aggregates signals."""

    def __init__(self, strategies: List[BaseStrategy]) -> None:
        self._strategies = strategies

    def add_strategy(self, strategy: BaseStrategy) -> None:
        self._strategies.append(strategy)

    def run(self, df: pd.DataFrame) -> List[Signal]:
        """Returns all non-neutral signals, sorted by confidence."""
        signals = []
        for strategy in self._strategies:
            try:
                signal = strategy.generate_signal(df)
                if signal.side != "none":
                    signals.append(signal)
                    logger.info(
                        "signal_generated",
                        strategy=strategy.name,
                        side=signal.side,
                        confidence=signal.confidence,
                        reason=signal.reason,
                    )
            except Exception as e:
                logger.error("strategy_error", strategy=strategy.name, error=str(e))

        return sorted(signals, key=lambda s: s.confidence, reverse=True)

    def best_signal(self, df: pd.DataFrame) -> Signal | None:
        """Returns highest-confidence signal, or None."""
        signals = self.run(df)
        return signals[0] if signals else None
