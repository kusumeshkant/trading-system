"""
Quick backtesting script. Run with:
  python scripts/backtest.py --symbol BTCUSDT --interval 1h --strategy ema
"""
import asyncio
import argparse
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.brokers.binance.client import BinanceClient
from app.services.market_data.ingestion import MarketDataService
from app.strategies.implementations.ema_crossover import EMACrossoverStrategy
from app.strategies.implementations.rsi_mean_reversion import RSIMeanReversionStrategy
from app.strategies.implementations.breakout_scalper import BreakoutScalperStrategy


STRATEGIES = {
    "ema": EMACrossoverStrategy(),
    "rsi": RSIMeanReversionStrategy(),
    "breakout": BreakoutScalperStrategy(),
}


async def run_backtest(symbol: str, interval: str, strategy_name: str, capital: float):
    broker = BinanceClient()
    await broker.connect()

    try:
        svc = MarketDataService(broker)
        df = await svc.get_ohlcv(symbol, interval, limit=500)
    finally:
        await broker.disconnect()

    strategy = STRATEGIES[strategy_name]
    trades = []
    balance = capital

    for i in range(50, len(df)):
        window = df.iloc[:i].copy()
        window.attrs["symbol"] = symbol
        signal = strategy.generate_signal(window)

        if signal.side == "none":
            continue

        # Simulate next-candle entry
        next_candle = df.iloc[i]
        entry = next_candle["open"]
        risk_per_trade = balance * 0.01  # 1% risk
        price_risk = abs(entry - signal.stop_loss)
        if price_risk == 0:
            continue
        qty = risk_per_trade / price_risk

        # Check if SL or TP hit within next 10 candles
        outcome = "open"
        pnl = 0.0
        for j in range(i + 1, min(i + 10, len(df))):
            c = df.iloc[j]
            if signal.side == "buy":
                if c["low"] <= signal.stop_loss:
                    pnl = -risk_per_trade
                    outcome = "sl_hit"
                    break
                if c["high"] >= signal.take_profit:
                    pnl = risk_per_trade * 2
                    outcome = "tp_hit"
                    break
            else:
                if c["high"] >= signal.stop_loss:
                    pnl = -risk_per_trade
                    outcome = "sl_hit"
                    break
                if c["low"] <= signal.take_profit:
                    pnl = risk_per_trade * 2
                    outcome = "tp_hit"
                    break

        balance += pnl
        trades.append({
            "index": i,
            "side": signal.side,
            "entry": entry,
            "outcome": outcome,
            "pnl": round(pnl, 2),
            "balance": round(balance, 2),
        })

    if not trades:
        print("No trades generated.")
        return

    results = pd.DataFrame(trades)
    wins = results[results["pnl"] > 0]
    losses = results[results["pnl"] < 0]

    print(f"\n=== BACKTEST: {strategy_name.upper()} on {symbol} {interval} ===")
    print(f"Total trades   : {len(results)}")
    print(f"Win rate       : {len(wins)/len(results)*100:.1f}%")
    print(f"Total PnL      : {results['pnl'].sum():.2f} USDT")
    print(f"Starting capital: {capital:.2f}")
    print(f"Final balance  : {balance:.2f}")
    print(f"Return         : {(balance - capital) / capital * 100:.2f}%")
    print(f"Max drawdown   : coming soon")
    print(results.tail(10).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--strategy", default="ema", choices=["ema", "rsi", "breakout"])
    parser.add_argument("--capital", type=float, default=20000)
    args = parser.parse_args()

    asyncio.run(run_backtest(args.symbol, args.interval, args.strategy, args.capital))
