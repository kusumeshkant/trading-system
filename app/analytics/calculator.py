from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np


def calculate_gross_pnl(entry: float, exit_price: float, qty: float, side: str) -> float:
    if side.lower() in ("long", "buy"):
        return (exit_price - entry) * qty
    return (entry - exit_price) * qty


def calculate_net_pnl(gross_pnl: float, fees: float, slippage: float) -> float:
    return gross_pnl - fees - slippage


def calculate_risk_reward(
    entry: float,
    stop_loss: Optional[float],
    take_profit: Optional[float],
    side: str,
) -> Optional[float]:
    if not stop_loss or not take_profit:
        return None
    if side.lower() in ("long", "buy"):
        risk = entry - stop_loss
        reward = take_profit - entry
    else:
        risk = stop_loss - entry
        reward = entry - take_profit
    if risk <= 0:
        return None
    return round(reward / risk, 2)


def calculate_duration_minutes(opened_at: datetime, closed_at: datetime) -> float:
    return (closed_at - opened_at).total_seconds() / 60


def calculate_max_drawdown(pnl_series: List[float]) -> float:
    if not pnl_series:
        return 0.0
    cumulative = np.cumsum(pnl_series)
    peak = np.maximum.accumulate(cumulative)
    drawdown = peak - cumulative
    return float(np.max(drawdown))


def calculate_profit_factor(gross_wins: float, gross_losses: float) -> float:
    if gross_losses == 0:
        return float("inf") if gross_wins > 0 else 0.0
    return abs(gross_wins / gross_losses)


def calculate_sharpe_ratio(
    returns: List[float], risk_free_rate: float = 0.0
) -> Optional[float]:
    if len(returns) < 2:
        return None
    arr = np.array(returns, dtype=float)
    excess = arr - risk_free_rate
    std = float(np.std(excess, ddof=1))
    if std == 0:
        return None
    return round(float(np.mean(excess) / std * np.sqrt(252)), 4)


def calculate_win_rate(wins: int, total: int) -> float:
    return round((wins / total) * 100, 2) if total > 0 else 0.0


def calculate_equity_curve(
    pnl_series: List[float], initial_capital: float = 10_000.0
) -> List[float]:
    curve = [initial_capital]
    for pnl in pnl_series:
        curve.append(round(curve[-1] + pnl, 4))
    return curve


def calculate_consecutive_streaks(results: List[bool]) -> Dict[str, int]:
    max_wins = max_losses = cur_wins = cur_losses = 0
    for r in results:
        if r:
            cur_wins += 1
            cur_losses = 0
            max_wins = max(max_wins, cur_wins)
        else:
            cur_losses += 1
            cur_wins = 0
            max_losses = max(max_losses, cur_losses)
    return {"max_consecutive_wins": max_wins, "max_consecutive_losses": max_losses}


def recommend_improvements(metrics: Dict[str, Any]) -> List[str]:
    recs: List[str] = []
    win_rate = metrics.get("win_rate", 0)
    avg_rr = metrics.get("avg_rr", 0)
    profit_factor = metrics.get("profit_factor", 0)
    max_drawdown = metrics.get("max_drawdown", 0)

    if win_rate < 40:
        recs.append("Win rate below 40% — review entry criteria and signal filters.")
    if 0 < avg_rr < 1.5:
        recs.append("Avg R:R below 1.5 — consider widening take-profit or tightening stop-loss.")
    if 0 < profit_factor < 1.5:
        recs.append("Profit factor below 1.5 — cut losing trades faster and let winners run.")
    if max_drawdown > 15:
        recs.append("Max drawdown exceeds 15% — reduce position sizing or add strategy filters.")

    if not recs:
        recs.append("All core metrics are within healthy ranges. Stay consistent.")
    return recs
