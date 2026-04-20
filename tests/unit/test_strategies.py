import pytest
import pandas as pd
import numpy as np
from app.strategies.implementations.ema_crossover import EMACrossoverStrategy
from app.strategies.implementations.rsi_mean_reversion import RSIMeanReversionStrategy


def make_df(n=200, trend="up"):
    """Generate synthetic OHLCV data."""
    np.random.seed(42)
    close = 50000 + np.cumsum(np.random.randn(n) * 100)
    if trend == "down":
        close = 50000 - np.cumsum(np.abs(np.random.randn(n) * 100))
    df = pd.DataFrame({
        "open": close * 0.999,
        "high": close * 1.002,
        "low": close * 0.998,
        "close": close,
        "volume": np.random.uniform(100, 500, n),
    })
    df.attrs["symbol"] = "BTCUSDT"
    return df


def test_ema_crossover_returns_signal():
    strategy = EMACrossoverStrategy()
    df = make_df(200)
    signal = strategy.generate_signal(df)
    assert signal.symbol == "BTCUSDT"
    assert signal.side in ("buy", "sell", "none")
    assert signal.strategy_name == "ema_crossover"


def test_ema_crossover_requires_enough_data():
    strategy = EMACrossoverStrategy()
    df = make_df(10)
    with pytest.raises(ValueError):
        strategy.generate_signal(df)


def test_rsi_returns_signal():
    strategy = RSIMeanReversionStrategy()
    df = make_df(300)
    signal = strategy.generate_signal(df)
    assert signal.strategy_name == "rsi_mean_reversion"


def test_signal_has_valid_rr():
    strategy = EMACrossoverStrategy()
    df = make_df(200)
    signal = strategy.generate_signal(df)
    if signal.side != "none":
        risk = abs(signal.entry_price - signal.stop_loss)
        reward = abs(signal.take_profit - signal.entry_price)
        assert reward >= risk  # minimum 1:1 RR
