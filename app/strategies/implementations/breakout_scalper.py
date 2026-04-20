"""
Breakout Scalper Strategy — AGGRESSIVE
----------------------------------------
Rule: Price breaks above 20-candle high with volume spike = BUY.
      Price breaks below 20-candle low with volume spike = SELL.
Works best on: BTC/USDT, ETH/USDT on 5m or 15m.
High frequency, tight stops. Use with leverage max 5x.
WARNING: High win-rate needed. Use only in trending markets.
"""
import pandas as pd
import pandas_ta as ta
from app.strategies.base.strategy import BaseStrategy, Signal


class BreakoutScalperStrategy(BaseStrategy):
    name = "breakout_scalper"
    risk_level = "aggressive"

    def __init__(self, lookback: int = 20, volume_multiplier: float = 1.5) -> None:
        self.lookback = lookback
        self.volume_multiplier = volume_multiplier

    def generate_signal(self, df: pd.DataFrame) -> Signal:
        self._validate_df(df)

        df = df.copy()
        df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)
        df["vol_ma"] = df["volume"].rolling(self.lookback).mean()

        latest = df.iloc[-1]
        prev_window = df.iloc[-(self.lookback + 1):-1]

        entry = latest["close"]
        atr = latest["atr"]
        resistance = prev_window["high"].max()
        support = prev_window["low"].min()
        vol_spike = latest["volume"] > (latest["vol_ma"] * self.volume_multiplier)

        if pd.isna(atr):
            return self._no_signal(df, entry)

        # Bullish breakout
        if entry > resistance and vol_spike:
            stop_loss = resistance - (0.5 * atr)   # tight stop below breakout level
            take_profit = entry + (2.0 * atr)
            return Signal(
                symbol=df.attrs.get("symbol", "UNKNOWN"),
                side="buy",
                entry_price=entry,
                stop_loss=round(stop_loss, 4),
                take_profit=round(take_profit, 4),
                confidence=0.60,
                strategy_name=self.name,
                reason=f"Breakout above {resistance:.4f} with volume spike",
            )

        # Bearish breakdown
        if entry < support and vol_spike:
            stop_loss = support + (0.5 * atr)
            take_profit = entry - (2.0 * atr)
            return Signal(
                symbol=df.attrs.get("symbol", "UNKNOWN"),
                side="sell",
                entry_price=entry,
                stop_loss=round(stop_loss, 4),
                take_profit=round(take_profit, 4),
                confidence=0.60,
                strategy_name=self.name,
                reason=f"Breakdown below {support:.4f} with volume spike",
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
            reason="No breakout detected",
        )
