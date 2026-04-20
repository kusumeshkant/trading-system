"""
EMA Crossover Strategy — LOW RISK
----------------------------------
Rule: EMA9 crosses above EMA21 = BUY. EMA9 crosses below EMA21 = SELL.
Works best on: BTC/USDT, ETH/USDT on 1h or 4h timeframe.
Stop loss: 1.5x ATR below entry.
Take profit: 2x risk (1:2 RR minimum).
"""
import pandas as pd
import pandas_ta as ta
from app.strategies.base.strategy import BaseStrategy, Signal


class EMACrossoverStrategy(BaseStrategy):
    name = "ema_crossover"
    risk_level = "low"

    def __init__(self, fast: int = 9, slow: int = 21, atr_period: int = 14) -> None:
        self.fast = fast
        self.slow = slow
        self.atr_period = atr_period

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        self._validate_df(df)

        df = df.copy()
        df["ema_fast"] = ta.ema(df["close"], length=self.fast)
        df["ema_slow"] = ta.ema(df["close"], length=self.slow)
        df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=self.atr_period)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        entry = latest["close"]
        atr = latest["atr"]

        # Bullish crossover
        if prev["ema_fast"] <= prev["ema_slow"] and latest["ema_fast"] > latest["ema_slow"]:
            stop_loss = entry - (1.5 * atr)
            take_profit = entry + (3.0 * atr)   # 1:2 RR
            return Signal(
                symbol=df.attrs.get("symbol", "UNKNOWN"),
                side="buy",
                entry_price=entry,
                stop_loss=round(stop_loss, 4),
                take_profit=round(take_profit, 4),
                confidence=0.65,
                strategy_name=self.name,
                reason=f"EMA{self.fast} crossed above EMA{self.slow}",
            )

        # Bearish crossover
        if prev["ema_fast"] >= prev["ema_slow"] and latest["ema_fast"] < latest["ema_slow"]:
            stop_loss = entry + (1.5 * atr)
            take_profit = entry - (3.0 * atr)
            return Signal(
                symbol=df.attrs.get("symbol", "UNKNOWN"),
                side="sell",
                entry_price=entry,
                stop_loss=round(stop_loss, 4),
                take_profit=round(take_profit, 4),
                confidence=0.65,
                strategy_name=self.name,
                reason=f"EMA{self.fast} crossed below EMA{self.slow}",
            )

        return Signal(
            symbol=df.attrs.get("symbol", "UNKNOWN"),
            side="none",
            entry_price=entry,
            stop_loss=0.0,
            take_profit=0.0,
            confidence=0.0,
            strategy_name=self.name,
            reason="No crossover detected",
        )
