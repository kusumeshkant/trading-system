from datetime import date
from typing import List
from app.analytics.models import TradeRecord, DailyReport
from app.analytics.calculator import (
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_win_rate,
    recommend_improvements,
)


def generate_daily_report(trades: List[TradeRecord], report_date: date) -> DailyReport:
    closed = [
        t for t in trades
        if t.closed_at and t.closed_at.date() == report_date and t.net_pnl is not None
    ]

    wins = [t for t in closed if t.net_pnl > 0]
    losses = [t for t in closed if t.net_pnl <= 0]
    net_pnls = [t.net_pnl for t in closed]

    gross_profit = sum(t.net_pnl for t in wins)
    gross_loss = sum(t.net_pnl for t in losses)

    best = max(closed, key=lambda t: t.net_pnl, default=None)
    worst = min(closed, key=lambda t: t.net_pnl, default=None)

    rr_values = [t.risk_reward_ratio for t in closed if t.risk_reward_ratio]
    avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0.0

    metrics = {
        "win_rate": calculate_win_rate(len(wins), len(closed)),
        "avg_rr": avg_rr,
        "profit_factor": calculate_profit_factor(gross_profit, abs(gross_loss)),
        "max_drawdown": calculate_max_drawdown(net_pnls),
    }

    return DailyReport(
        date=report_date,
        total_trades=len(closed),
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate=metrics["win_rate"],
        gross_profit=round(gross_profit, 4),
        gross_loss=round(gross_loss, 4),
        net_pnl=round(sum(net_pnls), 4) if net_pnls else 0.0,
        fees_paid=round(sum(t.fees_paid for t in closed), 4),
        best_trade_id=str(best.id) if best else None,
        worst_trade_id=str(worst.id) if worst else None,
        best_trade_pnl=round(best.net_pnl, 4) if best else None,
        worst_trade_pnl=round(worst.net_pnl, 4) if worst else None,
        max_drawdown=round(metrics["max_drawdown"], 4),
        avg_win=round(gross_profit / len(wins), 4) if wins else 0.0,
        avg_loss=round(gross_loss / len(losses), 4) if losses else 0.0,
        avg_rr=round(avg_rr, 2),
        profit_factor=round(metrics["profit_factor"], 2),
        mistakes_count=sum(1 for t in closed if t.mistakes),
        recommendations=recommend_improvements(metrics),
    )
