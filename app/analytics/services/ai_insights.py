"""
Rule-based AI insights engine — analyses trade history and surfaces actionable patterns.
"""
from collections import defaultdict
from typing import List, Dict, Any
from app.analytics.models import TradeRecord


def generate_insights(records: List[TradeRecord]) -> List[Dict[str, Any]]:
    closed = [t for t in records if t.net_pnl is not None]

    if len(closed) < 2:
        return [_i("info", "📊", "Need More Data",
                   "Log at least 2 closed trades to receive personalised insights.")]

    insights: List[Dict[str, Any]] = []
    wins = [t for t in closed if t.net_pnl > 0]
    losses = [t for t in closed if t.net_pnl <= 0]
    total = len(closed)
    win_rate = round(len(wins) / total * 100, 1)

    avg_win = sum(t.net_pnl for t in wins) / len(wins) if wins else 0
    avg_loss = abs(sum(t.net_pnl for t in losses) / len(losses)) if losses else 0

    # ── Win rate ──────────────────────────────────────────────────────────────
    if win_rate < 40:
        insights.append(_i("danger", "⚠️", "Low Win Rate",
            f"Win rate is {win_rate}% — below the 40% danger threshold. "
            f"Focus on higher-probability setups and eliminate impulsive entries."))
    elif win_rate >= 60:
        insights.append(_i("success", "🏆", "Strong Win Rate",
            f"Win rate of {win_rate}% is above 60%. "
            f"Your entry criteria are working — maintain discipline."))

    # ── Risk / Reward ─────────────────────────────────────────────────────────
    if wins and losses:
        rr = avg_win / avg_loss if avg_loss > 0 else 0
        if rr < 1.0:
            insights.append(_i("danger", "📉", "Poor Risk/Reward",
                f"Avg win ${avg_win:.2f} is less than avg loss ${avg_loss:.2f} (R:R = {rr:.2f}). "
                f"Move take-profits further or tighten stop-losses."))
        elif rr >= 2.0:
            insights.append(_i("success", "💪", "Excellent Risk/Reward",
                f"Avg win (${avg_win:.2f}) is {rr:.1f}× your avg loss (${avg_loss:.2f}). "
                f"This is professional-grade risk management."))

    # ── Strategy breakdown ────────────────────────────────────────────────────
    strats: dict = defaultdict(list)
    for t in closed:
        strats[t.strategy].append(t.net_pnl)

    if len(strats) > 1:
        best_s = max(strats, key=lambda s: sum(strats[s]))
        worst_s = min(strats, key=lambda s: sum(strats[s]))
        insights.append(_i("info", "🎯", "Best Strategy",
            f"'{best_s}' leads with ${sum(strats[best_s]):.2f} net P&L "
            f"across {len(strats[best_s])} trades."))
        if sum(strats[worst_s]) < 0:
            insights.append(_i("warning", "🔄", "Underperforming Strategy",
                f"'{worst_s}' is down ${abs(sum(strats[worst_s])):.2f}. "
                f"Consider pausing it until you identify the root cause."))

    # ── Pair performance ──────────────────────────────────────────────────────
    pairs: dict = defaultdict(list)
    for t in closed:
        pairs[t.asset].append(t.net_pnl)
    if len(pairs) > 1:
        best_p = max(pairs, key=lambda p: sum(pairs[p]))
        worst_p = min(pairs, key=lambda p: sum(pairs[p]))
        insights.append(_i("info", "💱", "Best Pair",
            f"{best_p} is your most profitable pair: ${sum(pairs[best_p]):.2f} total."))
        if sum(pairs[worst_p]) < 0:
            insights.append(_i("warning", "🚫", "Worst Pair",
                f"{worst_p} is consistently losing (${sum(pairs[worst_p]):.2f}). "
                f"Review your setup for this pair or avoid it temporarily."))

    # ── Best / worst trading hours ─────────────────────────────────────────────
    hours: dict = defaultdict(list)
    for t in closed:
        hours[t.opened_at.hour].append(t.net_pnl)
    if hours:
        best_h = max(hours, key=lambda h: sum(hours[h]))
        worst_h = min(hours, key=lambda h: sum(hours[h]))
        insights.append(_i("info", "⏰", "Best Trading Hour",
            f"{best_h:02d}:00–{(best_h+1)%24:02d}:00 UTC is your most profitable window "
            f"(${sum(hours[best_h]):.2f})."))
        if sum(hours[worst_h]) < 0 and len(hours[worst_h]) >= 2:
            insights.append(_i("warning", "🌙", "Avoid This Hour",
                f"{worst_h:02d}:00–{(worst_h+1)%24:02d}:00 UTC consistently hurts P&L "
                f"(${sum(hours[worst_h]):.2f}). Consider skipping this window."))

    # ── Current streak ────────────────────────────────────────────────────────
    streak_w = streak_l = 0
    for t in closed:
        if t.net_pnl > 0:
            streak_w += 1; streak_l = 0
        else:
            streak_l += 1; streak_w = 0

    if streak_l >= 3:
        insights.append(_i("danger", "🛑", f"{streak_l}-Trade Loss Streak",
            f"You are on a {streak_l}-trade losing streak. "
            f"Step back, review your last setups, and consider paper trading until "
            f"confidence and clarity return."))
    elif streak_w >= 3:
        insights.append(_i("success", "🔥", f"{streak_w}-Trade Win Streak",
            f"You are on a {streak_w}-trade winning streak! "
            f"Stay disciplined — do not increase position size on emotion alone."))

    # ── Recent vs all-time ────────────────────────────────────────────────────
    if len(closed) >= 6:
        recent = closed[-5:]
        recent_wr = round(sum(1 for t in recent if t.net_pnl > 0) / 5 * 100, 1)
        if recent_wr < win_rate - 20:
            insights.append(_i("warning", "📊", "Performance Declining",
                f"Last 5 trades: {recent_wr}% win rate vs all-time {win_rate}%. "
                f"Review recent setups — something may have shifted in your approach."))
        elif recent_wr > win_rate + 20:
            insights.append(_i("success", "📈", "Momentum Building",
                f"Last 5 trades: {recent_wr}% win rate vs all-time {win_rate}%. "
                f"Good momentum — identify what's working and replicate it."))

    # ── Market condition ──────────────────────────────────────────────────────
    conditions: dict = defaultdict(list)
    for t in closed:
        if t.market_condition:
            conditions[t.market_condition.value].append(t.net_pnl)
    if len(conditions) >= 2:
        best_c = max(conditions, key=lambda c: sum(conditions[c]))
        worst_c = min(conditions, key=lambda c: sum(conditions[c]))
        best_label = best_c.replace("_", " ").title()
        worst_label = worst_c.replace("_", " ").title()
        insights.append(_i("info", "🌡️", "Optimal Market Condition",
            f"You perform best in '{best_label}' conditions "
            f"and worst in '{worst_label}' — filter your entries accordingly."))

    # ── Overtrading ───────────────────────────────────────────────────────────
    if len(closed) >= 10:
        days = max(1, (closed[-1].opened_at - closed[0].opened_at).days)
        tpd = len(closed) / days
        if tpd > 5:
            insights.append(_i("warning", "⚡", "Possible Overtrading",
                f"You average {tpd:.1f} trades/day. "
                f"Overtrading leads to emotional decisions and eroded edge. Quality > quantity."))

    # ── Long vs Short performance ─────────────────────────────────────────────
    longs = [t for t in closed if t.trade_type and t.trade_type.value in ("long", "buy")]
    shorts = [t for t in closed if t.trade_type and t.trade_type.value in ("short", "sell")]
    if longs and shorts:
        long_pnl = sum(t.net_pnl for t in longs)
        short_pnl = sum(t.net_pnl for t in shorts)
        better = "Long" if long_pnl > short_pnl else "Short"
        diff = abs(long_pnl - short_pnl)
        insights.append(_i("info", "↕️", "Long vs Short Bias",
            f"{better} trades outperform by ${diff:.2f} total. "
            f"Consider weighting more of your entries toward {better.lower()} setups."))

    return insights or [_i("success", "✅", "No Issues Found",
        "Keep logging trades for deeper pattern recognition and personalised insights.")]


def _i(type_: str, icon: str, title: str, message: str) -> Dict[str, Any]:
    return {"type": type_, "icon": icon, "title": title, "message": message}
