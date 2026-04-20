# Phase 1 — Manual Trading Guide (Next 72 Hours)

## Reality Check

| Scenario | Probability | Outcome on 20,000 |
|----------|-------------|-------------------|
| Make 60k (200% return) | ~3-5% | Requires perfect trades + luck |
| Make 5-20k (25-100%) | ~25% | Realistic best case |
| Break even | ~20% | No gain, no loss |
| Lose 20-50% (4-10k) | ~40% | Likely without discipline |
| Lose 80-100% | ~10-15% | Going all-in / no stop loss |

**If rent MUST be paid:** Consider this money already at risk. Do not use it if losing it causes a crisis.

---

## Best Pairs to Trade (Binance)

| Pair | Why | Timeframe |
|------|-----|-----------|
| BTC/USDT | Most liquid, reliable TA | 1h, 4h |
| ETH/USDT | High volatility, good signals | 1h |
| SOL/USDT | Fast moves, good for scalping | 15m |
| BNB/USDT | Steady trends | 1h |

**Avoid:** Low cap altcoins, meme coins, leverage > 5x

---

## 3 Strategies

### 1. EMA Crossover (LOW RISK)
- **Entry:** EMA9 crosses above EMA21 = BUY
- **Timeframe:** 1h or 4h
- **Stop Loss:** 1.5x ATR below entry
- **Take Profit:** 3x ATR above entry (1:2 RR)
- **Expected:** 2-4 signals/day
- **Win rate:** ~55-60%

### 2. RSI Mean Reversion (MEDIUM RISK)
- **Entry:** RSI < 30 = BUY, RSI > 70 = SELL
- **Condition:** Price must be above/below EMA200
- **Timeframe:** 15m or 1h
- **Stop Loss:** 1x ATR
- **Take Profit:** 2x ATR (1:2 RR)
- **Expected:** 1-3 signals/day

### 3. Breakout Scalper (AGGRESSIVE)
- **Entry:** Price breaks 20-candle high/low + volume spike
- **Timeframe:** 5m or 15m
- **Stop Loss:** Very tight — 0.5x ATR below breakout
- **Take Profit:** 2x ATR
- **Expected:** 3-8 signals/day
- **Warning:** High frequency = high emotion risk

---

## Position Sizing Formula

```
Risk per trade = Capital × 1%  = 20,000 × 0.01 = 200
Price risk     = Entry - Stop Loss
Quantity       = Risk / Price risk
```

**Example:**
- BTC at 65,000, Stop at 64,350 → Price risk = 650
- Quantity = 200 / 650 = 0.307 BTC

---

## Capital Protection Rules

1. **Max 1% risk per trade** — never more
2. **Max 3 open trades at once**
3. **Daily loss limit: 5%** (1,000 on 20k) — stop for the day
4. **No leverage above 5x**
5. **Never average down on a losing trade**
6. **If you miss the entry, skip the trade**
7. **Trade WITH the 4h trend, not against it**
8. **No trading 30 min before/after major news (CPI, FOMC)**

---

## Pre-Trade Checklist

- [ ] What is the 4h trend direction?
- [ ] Is there major news in the next 2 hours?
- [ ] What is my daily P&L so far today?
- [ ] Do I have less than 3 open trades?
- [ ] Is my stop loss placed BEFORE entry?
- [ ] Am I calm or emotional right now?
- [ ] Is the risk:reward at least 1:2?

---

## Markets to Avoid

- During low volume (00:00-06:00 UTC on weekdays)
- Before/after major economic events
- When BTC dominance is rapidly changing
- During exchange outages or unusual spreads
- If you feel anxious, angry, or desperate

---

## 72-Hour Action Plan

### Day 1 (Hours 1-8)
- [ ] Run `phase1_manual_assistant.py`
- [ ] Watch signals for first 2 hours WITHOUT trading
- [ ] Paper trade 3 signals manually
- [ ] Backtest EMA strategy: `python scripts/backtest.py --strategy ema`

### Day 1 (Hours 8-16)
- [ ] If paper trading went well, go live with 1% risk trades
- [ ] Max 3 trades for the day
- [ ] Log every trade in journal

### Day 2
- [ ] Review yesterday's journal
- [ ] Identify what worked
- [ ] Stick to best-performing strategy only
- [ ] Do not increase risk even if winning

### Day 3
- [ ] Same discipline as Day 2
- [ ] Do not chase losses
- [ ] Stop at daily loss limit

---

## Emotional Trading Mistakes to Avoid

| Mistake | What it looks like | Fix |
|---------|-------------------|-----|
| Revenge trading | Doubling size after a loss | Stop for 2 hours minimum |
| FOMO | Entering after price already moved 3% | Skip that trade |
| Moving stop loss | "It'll come back" | Never touch SL after entry |
| Overtrading | Taking every minor move | Only take confirmed signals |
| Greed | Removing TP because "it'll go higher" | Set and forget |
