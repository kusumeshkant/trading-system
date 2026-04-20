"""
PHASE 1 — Manual Trading Assistant
------------------------------------
Run this script right now to get real-time signals.
It does NOT place orders. YOU decide to trade.

Usage:
  python scripts/phase1_manual_assistant.py

It will:
  - Fetch live data from Binance
  - Run all 3 strategies
  - Print clear BUY/SELL signals with entry, SL, TP
  - Repeat every 5 minutes
"""
import asyncio
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.brokers.binance.client import BinanceClient
from app.services.market_data.ingestion import MarketDataService
from app.services.signals.engine import SignalEngine
from app.strategies.implementations.ema_crossover import EMACrossoverStrategy
from app.strategies.implementations.rsi_mean_reversion import RSIMeanReversionStrategy
from app.strategies.implementations.breakout_scalper import BreakoutScalperStrategy

WATCHLIST = [
    ("BTCUSDT", "1h"),
    ("ETHUSDT", "1h"),
    ("BNBUSDT", "1h"),
    ("SOLUSDT", "15m"),
]

CAPITAL = 20_000        # your INR capital (treat as units)
RISK_PERCENT = 1.0      # risk 1% per trade = 200 units max loss per trade
MAX_DAILY_LOSS = 1_000  # hard stop for the day


def print_signal(symbol, interval, signal):
    risk = abs(signal.entry_price - signal.stop_loss)
    reward = abs(signal.take_profit - signal.entry_price)
    rr = reward / risk if risk > 0 else 0
    qty = (CAPITAL * RISK_PERCENT / 100) / risk if risk > 0 else 0

    print(f"""
{'='*55}
  {signal.side.upper()} SIGNAL — {symbol} ({interval})
{'='*55}
  Strategy   : {signal.strategy_name}
  Reason     : {signal.reason}
  Confidence : {signal.confidence * 100:.0f}%

  Entry      : {signal.entry_price:.4f}
  Stop Loss  : {signal.stop_loss:.4f}  (risk: {risk:.4f})
  Take Profit: {signal.take_profit:.4f}  (reward: {reward:.4f})
  Risk:Reward: 1:{rr:.1f}

  Suggested qty (1% risk on {CAPITAL}): {qty:.4f}

  ACTION REQUIRED — YOU must place this manually on Binance.
{'='*55}
""")


async def scan_once():
    broker = BinanceClient()
    await broker.connect()

    engine = SignalEngine([
        EMACrossoverStrategy(),
        RSIMeanReversionStrategy(),
        BreakoutScalperStrategy(),
    ])

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning {len(WATCHLIST)} pairs...")
    found = 0

    try:
        for symbol, interval in WATCHLIST:
            svc = MarketDataService(broker)
            df = await svc.get_ohlcv(symbol, interval)
            signal = engine.best_signal(df)
            if signal:
                print_signal(symbol, interval, signal)
                found += 1
    finally:
        await broker.disconnect()

    if found == 0:
        print("  No signals right now. Market is neutral. Wait.")


async def main():
    print("""
╔══════════════════════════════════════╗
║   PHASE 1 — Manual Trading Assistant ║
║   Capital: 20,000  |  Risk: 1%/trade ║
║   Max daily loss: 1,000              ║
╚══════════════════════════════════════╝

RULES (read before trading):
  1. Max 3 trades open at once
  2. Never risk more than 1% per trade
  3. If daily loss hits 1,000 — STOP for the day
  4. Trade WITH the trend (check 4h chart direction first)
  5. Avoid trading 30 min before/after major news
  6. No revenge trading after a loss

Press Ctrl+C to stop.
""")

    while True:
        try:
            await scan_once()
        except Exception as e:
            print(f"Error: {e}")
        print("\nNext scan in 5 minutes...")
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())
