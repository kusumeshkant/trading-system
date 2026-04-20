from datetime import date
from typing import List, Dict
from collections import defaultdict
from app.analytics.models import TradeRecord, WeeklyReport, MonthlyReport
from app.analytics.calculator import (
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_win_rate,
    calculate_equity_curve,
    calculate_consecutive_streaks,
    calculate_sharpe_ratio,
    recommend_improvements,
)


def _breakdown_by(trades: List[TradeRecord], key_fn) -> Dict:
    groups: Dict[str, List[TradeRecord]] = defaultdict(list)
    for t in trades:
        groups[key_fn(t)].append(t)
    result = {}
    for k, group in groups.items():
        wins = [t for t in group if t.net_pnl and t.net_pnl > 0]
        result[k] = {
            "trades": len(group),
            "wins": len(wins),
            "losses": len(group) - len(wins),
            "win_rate": calculate_win_rate(len(wins), len(group)),
            "net_pnl": round(sum(t.net_pnl for t in group if t.net_pnl), 4),
            "avg_rr": round(
                sum(t.risk_reward_ratio for t in group if t.risk_reward_ratio)
                / max(sum(1 for t in group if t.risk_reward_ratio), 1),
                2,
            ),
        }
    return result


def generate_weekly_report(
    trades: List[TradeRecord], week_start: date, week_end: date
) -> WeeklyReport:
    closed = [
        t for t in trades
        if t.closed_at
        and week_start <= t.closed_at.date() <= week_end
        and t.net_pnl is not None
    ]

    wins = [t for t in closed if t.net_pnl > 0]
    losses = [t for t in closed if t.net_pnl <= 0]
    net_pnls = [t.net_pnl for t in closed]
    results = [t.net_pnl > 0 for t in closed]

    rr_values = [t.risk_reward_ratio for t in closed if t.risk_reward_ratio]
    avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0.0

    gross_profit = sum(t.net_pnl for t in wins)
    gross_loss = sum(t.net_pnl for t in losses)
    streaks = calculate_consecutive_streaks(results)

    hourly: Dict[str, List[float]] = defaultdict(list)
    for t in closed:
        hourly[str(t.opened_at.hour)].append(t.net_pnl)
    hourly_breakdown = {
        h: {"trades": len(v), "net_pnl": round(sum(v), 4)}
        for h, v in hourly.items()
    }

    metrics = {
        "win_rate": calculate_win_rate(len(wins), len(closed)),
        "avg_rr": avg_rr,
        "profit_factor": calculate_profit_factor(gross_profit, abs(gross_loss)),
        "max_drawdown": calculate_max_drawdown(net_pnls),
    }

    return WeeklyReport(
        week_start=week_start,
        week_end=week_end,
        total_trades=len(closed),
        win_rate=metrics["win_rate"],
        net_pnl=round(sum(net_pnls), 4) if net_pnls else 0.0,
        avg_rr=round(avg_rr, 2),
        max_drawdown=round(metrics["max_drawdown"], 4),
        profit_factor=round(metrics["profit_factor"], 2),
        max_consecutive_wins=streaks["max_consecutive_wins"],
        max_consecutive_losses=streaks["max_consecutive_losses"],
        strategy_breakdown=_breakdown_by(closed, lambda t: t.strategy),
        pair_breakdown=_breakdown_by(closed, lambda t: t.asset),
        hourly_breakdown=hourly_breakdown,
        equity_curve=calculate_equity_curve(net_pnls),
        improvement_suggestions=recommend_improvements(metrics),
    )


def generate_monthly_report(
    trades: List[TradeRecord], year: int, month: int
) -> MonthlyReport:
    closed = [
        t for t in trades
        if t.closed_at
        and t.closed_at.year == year
        and t.closed_at.month == month
        and t.net_pnl is not None
    ]

    wins = [t for t in closed if t.net_pnl > 0]
    losses = [t for t in closed if t.net_pnl <= 0]
    net_pnls = [t.net_pnl for t in closed]

    rr_values = [t.risk_reward_ratio for t in closed if t.risk_reward_ratio]
    avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0.0
    gross_profit = sum(t.net_pnl for t in wins)
    gross_loss = sum(t.net_pnl for t in losses)

    hourly: Dict[str, List[float]] = defaultdict(list)
    for t in closed:
        hourly[str(t.opened_at.hour)].append(t.net_pnl)
    hourly_breakdown = {
        h: {"trades": len(v), "net_pnl": round(sum(v), 4)}
        for h, v in hourly.items()
    }

    loss_patterns: Dict[str, int] = defaultdict(int)
    for t in losses:
        loss_patterns[t.closed_at.strftime("%A")] += 1

    metrics = {
        "win_rate": calculate_win_rate(len(wins), len(closed)),
        "avg_rr": avg_rr,
        "profit_factor": calculate_profit_factor(gross_profit, abs(gross_loss)),
        "max_drawdown": calculate_max_drawdown(net_pnls),
    }

    return MonthlyReport(
        year=year,
        month=month,
        total_trades=len(closed),
        win_rate=metrics["win_rate"],
        net_pnl=round(sum(net_pnls), 4) if net_pnls else 0.0,
        avg_rr=round(avg_rr, 2),
        max_drawdown=round(metrics["max_drawdown"], 4),
        profit_factor=round(metrics["profit_factor"], 2),
        sharpe_ratio=calculate_sharpe_ratio(net_pnls),
        strategy_breakdown=_breakdown_by(closed, lambda t: t.strategy),
        pair_breakdown=_breakdown_by(closed, lambda t: t.asset),
        hourly_breakdown=hourly_breakdown,
        loss_patterns=dict(loss_patterns),
        equity_curve=calculate_equity_curve(net_pnls),
        improvement_suggestions=recommend_improvements(metrics),
    )
