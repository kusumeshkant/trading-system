"""
RSI Mean Reversion Strategy — MEDIUM RISK
------------------------------------------
Rule: RSI < 30 and price above 200 EMA = oversold BUY opportunity.
      RSI > 70 and price below 200 EMA = overbought SELL opportunity.
Works best on: BTC/USDT, ETH/USDT, BNB/USDT on 15m or 1h.
"""
import pandas as pd
import pandas_ta as ta
from app.strategies.base.strategy import BaseStrategy, Signal


class RSIMeanReversionStrategy(BaseStrategy):
    name = "rsi_mean_reversion"
    risk_level = "medium"

    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70) -> None:
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        self._validate_df(df)

        df = df.copy()
        df["rsi"] = ta.rsi(df["close"], length=self.rsi_period)
        df["ema200"] = ta.ema(df["close"], length=200)
        df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)

        latest = df.iloc[-1]
        entry = latest["close"]
        atr = latest["atr"]
        rsi = latest["rsi"]
        ema200 = latest["ema200"]

        if pd.isna(ema200) or pd.isna(rsi) or pd.isna(atr):
            return self._no_signal(df, entry)

        # Oversold bounce — buy
        if rsi < self.oversold and entry > ema200:
            stop_loss = entry - (1.0 * atr)
            take_profit = entry + (2.0 * atr)
            return Signal(
                symbol=df.attrs.get("symbol", "UNKNOWN"),
                side="buy",
                entry_price=entry,
                stop_loss=round(stop_loss, 4),
                take_profit=round(take_profit, 4),
                confidence=0.70,
                strategy_name=self.name,
                reason=f"RSI {rsi:.1f} oversold, price above EMA200",
            )

        # Overbought rejection — sell
        if rsi > self.overbought and entry < ema200:
            stop_loss = entry + (1.0 * atr)
            take_profit = entry - (2.0 * atr)
            return Signal(
                symbol=df.attrs.get("symbol", "UNKNOWN"),
                side="sell",
                entry_price=entry,
                stop_loss=round(stop_loss, 4),
                take_profit=round(take_profit, 4),
                confidence=0.70,
                strategy_name=self.name,
                reason=f"RSI {rsi:.1f} overbought, price below EMA200",
            )

        return self._no_signal(df, entry)

    def _no_signal(self, df: pd.DataFrame, entry: float) -> Signal:
        return Signal(
            symbol=df.attrs.get("symbol", "UNKNOWN"),
            side="none",
            entry_price=entry,
            stop_loss=0.0,
            take_profit=0.0,
            confidence=0.0,
            strategy_name=self.name,
            reason="RSI in neutral zone",
        )
