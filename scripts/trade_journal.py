"""
Trade Journal — log your manual trades here.
Run: python scripts/trade_journal.py
"""
import json
import os
from datetime import datetime

JOURNAL_FILE = "trade_journal.json"


def load_journal():
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE) as f:
            return json.load(f)
    return []


def save_journal(trades):
    with open(JOURNAL_FILE, "w") as f:
        json.dump(trades, f, indent=2)


def log_trade():
    print("\n--- Log New Trade ---")
    trade = {
        "date": datetime.now().isoformat(),
        "symbol": input("Symbol (e.g. BTCUSDT): ").strip(),
        "side": input("Side (buy/sell): ").strip(),
        "entry": float(input("Entry price: ")),
        "stop_loss": float(input("Stop loss: ")),
        "take_profit": float(input("Take profit: ")),
        "quantity": float(input("Quantity: ")),
        "strategy": input("Strategy used: ").strip(),
        "reason": input("Why did you take this trade?: ").strip(),
        "exit_price": None,
        "pnl": None,
        "status": "open",
        "emotion_before": input("Emotion before trade (calm/anxious/greedy): ").strip(),
    }
    trades = load_journal()
    trades.append(trade)
    save_journal(trades)
    print(f"Trade logged. Total trades: {len(trades)}")


def close_trade():
    trades = load_journal()
    open_trades = [t for t in trades if t["status"] == "open"]
    if not open_trades:
        print("No open trades.")
        return
    for i, t in enumerate(open_trades):
        print(f"{i}: {t['symbol']} {t['side']} @ {t['entry']}")
    idx = int(input("Which trade to close? (number): "))
    trade = open_trades[idx]
    trade["exit_price"] = float(input("Exit price: "))
    trade["emotion_after"] = input("Emotion after (satisfied/regret/calm): ").strip()
    trade["lesson"] = input("What did you learn?: ").strip()

    if trade["side"] == "buy":
        pnl = (trade["exit_price"] - trade["entry"]) * trade["quantity"]
    else:
        pnl = (trade["entry"] - trade["exit_price"]) * trade["quantity"]

    trade["pnl"] = round(pnl, 4)
    trade["status"] = "closed"
    save_journal(trades)
    print(f"Trade closed. PnL: {pnl:+.4f}")


def show_stats():
    trades = load_journal()
    closed = [t for t in trades if t["status"] == "closed"]
    if not closed:
        print("No closed trades yet.")
        return
    wins = [t for t in closed if t["pnl"] > 0]
    total_pnl = sum(t["pnl"] for t in closed)
    print(f"\n=== JOURNAL STATS ===")
    print(f"Total trades : {len(closed)}")
    print(f"Win rate     : {len(wins)/len(closed)*100:.1f}%")
    print(f"Total PnL    : {total_pnl:+.4f}")
    print(f"Best trade   : {max(t['pnl'] for t in closed):+.4f}")
    print(f"Worst trade  : {min(t['pnl'] for t in closed):+.4f}")


def main():
    print("Trade Journal")
    print("1. Log new trade")
    print("2. Close a trade")
    print("3. Show stats")
    choice = input("Choice: ").strip()
    if choice == "1":
        log_trade()
    elif choice == "2":
        close_trade()
    elif choice == "3":
        show_stats()


if __name__ == "__main__":
    main()
