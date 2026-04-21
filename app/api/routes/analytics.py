from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from dataclasses import asdict
import uuid

from app.analytics.models import TradeRecord, TradeType, ExitReason, MarketCondition
from app.analytics.calculator import (
    calculate_gross_pnl, calculate_net_pnl, calculate_risk_reward,
    calculate_duration_minutes, calculate_equity_curve,
    calculate_win_rate, calculate_max_drawdown, calculate_profit_factor,
    calculate_sharpe_ratio,
)
from app.analytics.reports.trade_report import generate_trade_report
from app.analytics.reports.daily_report import generate_daily_report
from app.analytics.reports.periodic_report import generate_weekly_report, generate_monthly_report
from app.analytics.exporters.csv_exporter import export_trades_csv, export_daily_summaries_csv
from app.analytics.exporters.excel_exporter import export_trades_excel
from app.analytics.exporters.pdf_exporter import export_trade_pdf, export_daily_pdf, export_monthly_pdf
from app.analytics.dashboard.charts import (
    equity_curve_chart, drawdown_chart, pnl_bar_chart, strategy_performance_chart,
    win_loss_pie_chart, hourly_heatmap, rr_distribution_chart, pair_performance_chart,
)
from app.analytics.notifications.telegram_sender import (
    send_telegram_report, format_daily_telegram, format_trade_closed_telegram, format_weekly_telegram,
)
from app.analytics.notifications.email_sender import send_email_report, build_daily_email_html

from app.analytics.db import init_db, save_trade, delete_trade as db_delete, load_all_trades
router = APIRouter(prefix="/analytics", tags=["analytics"])

init_db()

def _records() -> List[TradeRecord]:
    return load_all_trades()


# ─── Schemas ───────────────────────────────────────────────────────────────────

class TradeRecordIn(BaseModel):
    trade_id: Optional[str] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None
    asset: str = Field(..., example="BTCUSDT")
    strategy: str = Field(..., example="EMA Crossover")
    trade_type: TradeType
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    quantity: float
    fees_paid: float = 0.0
    slippage: float = 0.0
    signal_reason: Optional[str] = None
    exit_reason: Optional[ExitReason] = None
    market_condition: Optional[MarketCondition] = None
    screenshot_url: Optional[str] = None
    notes: Optional[str] = None
    emotions: Optional[str] = None
    mistakes: Optional[str] = None
    broker: Optional[str] = None
    mode: str = "paper"
    tags: Optional[List[str]] = None


# ─── Trade CRUD ────────────────────────────────────────────────────────────────

@router.post("/trades", summary="Record a trade and get its full report")
async def record_trade(body: TradeRecordIn):
    record = TradeRecord(id=uuid.uuid4(), **body.model_dump())

    if record.exit_price is not None:
        gross = calculate_gross_pnl(
            record.entry_price, record.exit_price, record.quantity, record.trade_type.value
        )
        record.gross_pnl = round(gross, 6)
        record.net_pnl = round(calculate_net_pnl(gross, record.fees_paid, record.slippage), 6)
        if record.entry_price:
            record.pnl_percent = round(gross / (record.entry_price * record.quantity) * 100, 4)

    record.risk_reward_ratio = calculate_risk_reward(
        record.entry_price, record.stop_loss, record.take_profit, record.trade_type.value
    )
    if record.closed_at:
        record.trade_duration_minutes = round(
            calculate_duration_minutes(record.opened_at, record.closed_at), 2
        )

    save_trade(record)
    return asdict(generate_trade_report(record))


@router.get("/trades", summary="List all recorded trades")
async def list_trades(
    asset: Optional[str] = None,
    strategy: Optional[str] = None,
    mode: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    result = _records()
    if asset:
        result = [t for t in result if t.asset == asset]
    if strategy:
        result = [t for t in result if t.strategy == strategy]
    if mode:
        result = [t for t in result if t.mode == mode]
    return [asdict(generate_trade_report(t)) for t in result[-limit:]]


@router.get("/trades/{trade_id}", summary="Get full report for one trade")
async def get_trade(trade_id: str):
    record = _find(trade_id)
    return asdict(generate_trade_report(record))


@router.delete("/trades/{trade_id}", summary="Remove a trade record")
async def remove_trade(trade_id: str):
    record = _find(trade_id)
    db_delete(str(record.id))
    return {"deleted": trade_id}


# ─── Per-Trade Exports ─────────────────────────────────────────────────────────

@router.get("/trades/{trade_id}/pdf", summary="Download single trade PDF")
async def trade_pdf(trade_id: str):
    report = generate_trade_report(_find(trade_id))
    pdf = export_trade_pdf(report)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=trade_{trade_id[:8]}.pdf"})


# ─── Daily Reports ─────────────────────────────────────────────────────────────

@router.get("/reports/daily", summary="Daily summary report")
async def daily_report(d: str = Query(..., description="YYYY-MM-DD")):
    report_date = _parse_date(d)
    r = generate_daily_report(_records(), report_date)
    return _daily_dict(r)


@router.get("/reports/daily/pdf", summary="Daily report as PDF")
async def daily_pdf(d: str = Query(..., description="YYYY-MM-DD")):
    r = generate_daily_report(_records(), _parse_date(d))
    pdf = export_daily_pdf(_daily_dict(r))
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=daily_{d}.pdf"})


# ─── Weekly Reports ────────────────────────────────────────────────────────────

@router.get("/reports/weekly", summary="Weekly summary report")
async def weekly_report(
    start: str = Query(..., description="Week start YYYY-MM-DD"),
    end: str = Query(..., description="Week end YYYY-MM-DD"),
):
    r = generate_weekly_report(_records(), _parse_date(start), _parse_date(end))
    return {
        "week_start": str(r.week_start), "week_end": str(r.week_end),
        "total_trades": r.total_trades, "win_rate": r.win_rate,
        "net_pnl": r.net_pnl, "avg_rr": r.avg_rr,
        "max_drawdown": r.max_drawdown, "profit_factor": r.profit_factor,
        "max_consecutive_wins": r.max_consecutive_wins,
        "max_consecutive_losses": r.max_consecutive_losses,
        "strategy_breakdown": r.strategy_breakdown,
        "pair_breakdown": r.pair_breakdown,
        "hourly_breakdown": r.hourly_breakdown,
        "equity_curve": r.equity_curve,
        "improvement_suggestions": r.improvement_suggestions,
    }


# ─── Monthly Reports ───────────────────────────────────────────────────────────

@router.get("/reports/monthly", summary="Monthly summary report")
async def monthly_report(year: int, month: int = Query(..., ge=1, le=12)):
    r = generate_monthly_report(_records(), year, month)
    return {
        "year": r.year, "month": r.month,
        "total_trades": r.total_trades, "win_rate": r.win_rate,
        "net_pnl": r.net_pnl, "avg_rr": r.avg_rr,
        "max_drawdown": r.max_drawdown, "profit_factor": r.profit_factor,
        "sharpe_ratio": r.sharpe_ratio,
        "strategy_breakdown": r.strategy_breakdown,
        "pair_breakdown": r.pair_breakdown,
        "hourly_breakdown": r.hourly_breakdown,
        "loss_patterns": r.loss_patterns,
        "equity_curve": r.equity_curve,
        "improvement_suggestions": r.improvement_suggestions,
    }


@router.get("/reports/monthly/pdf", summary="Monthly report as PDF")
async def monthly_pdf(year: int, month: int = Query(..., ge=1, le=12)):
    r = generate_monthly_report(_records(), year, month)
    summary = {
        "year": r.year, "month": r.month,
        "total_trades": r.total_trades, "win_rate": r.win_rate,
        "net_pnl": r.net_pnl, "avg_rr": r.avg_rr,
        "max_drawdown": r.max_drawdown, "profit_factor": r.profit_factor,
        "sharpe_ratio": r.sharpe_ratio,
        "strategy_breakdown": r.strategy_breakdown,
        "improvement_suggestions": r.improvement_suggestions,
    }
    pdf = export_monthly_pdf(summary)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=monthly_{year}_{month:02d}.pdf"})


# ─── Overall KPIs ──────────────────────────────────────────────────────────────

@router.get("/kpis", summary="Overall performance KPIs")
async def kpis():
    closed = [t for t in _records() if t.net_pnl is not None]
    if not closed:
        return {"message": "No closed trades yet", "total_trades": 0}

    wins = [t for t in closed if t.net_pnl > 0]
    losses = [t for t in closed if t.net_pnl <= 0]
    net_pnls = [t.net_pnl for t in closed]
    rr_vals = [t.risk_reward_ratio for t in closed if t.risk_reward_ratio]
    gp = sum(t.net_pnl for t in wins)
    gl = sum(t.net_pnl for t in losses)

    return {
        "total_trades": len(closed),
        "open_trades": sum(1 for t in _records() if t.net_pnl is None),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate_pct": calculate_win_rate(len(wins), len(closed)),
        "total_net_pnl": round(sum(net_pnls), 4),
        "avg_net_pnl_per_trade": round(sum(net_pnls) / len(net_pnls), 4),
        "best_trade_pnl": round(max(net_pnls), 4),
        "worst_trade_pnl": round(min(net_pnls), 4),
        "avg_win": round(gp / len(wins), 4) if wins else 0,
        "avg_loss": round(gl / len(losses), 4) if losses else 0,
        "avg_rr": round(sum(rr_vals) / len(rr_vals), 2) if rr_vals else None,
        "profit_factor": round(calculate_profit_factor(gp, abs(gl)), 2),
        "max_drawdown": round(calculate_max_drawdown(net_pnls), 4),
        "sharpe_ratio": calculate_sharpe_ratio(net_pnls),
        "total_fees": round(sum(t.fees_paid for t in closed), 4),
        "total_slippage": round(sum(t.slippage for t in closed), 4),
    }


# ─── Exports ───────────────────────────────────────────────────────────────────

@router.get("/export/csv", summary="Export all trades as CSV")
async def export_csv():
    reports = [generate_trade_report(t) for t in _records()]
    data = export_trades_csv(reports)
    return Response(data, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=trades.csv"})


@router.get("/export/excel", summary="Export trades + daily summary as Excel")
async def export_excel():
    reports = [generate_trade_report(t) for t in _records()]
    trade_dates = sorted(set(t.opened_at.date() for t in _records()))
    daily = [_daily_dict(generate_daily_report(_records(), d)) for d in trade_dates]
    data = export_trades_excel(reports, daily)
    return Response(
        data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=trading_report.xlsx"},
    )


# ─── Dashboard Charts ──────────────────────────────────────────────────────────

@router.get("/charts/equity", summary="Equity curve PNG")
async def chart_equity():
    pnls = [t.net_pnl for t in _records() if t.net_pnl is not None]
    return Response(equity_curve_chart(calculate_equity_curve(pnls)), media_type="image/png")


@router.get("/charts/drawdown", summary="Drawdown PNG")
async def chart_drawdown():
    pnls = [t.net_pnl for t in _records() if t.net_pnl is not None]
    return Response(drawdown_chart(calculate_equity_curve(pnls)), media_type="image/png")


@router.get("/charts/winloss", summary="Win/Loss pie PNG")
async def chart_winloss():
    wins = sum(1 for t in _records() if t.net_pnl is not None and t.net_pnl > 0)
    losses = sum(1 for t in _records() if t.net_pnl is not None and t.net_pnl <= 0)
    return Response(win_loss_pie_chart(wins, losses), media_type="image/png")


@router.get("/charts/daily-pnl", summary="Daily P&L bar PNG")
async def chart_daily_pnl():
    from collections import defaultdict
    daily: dict = defaultdict(list)
    for t in _records():
        if t.net_pnl is not None:
            daily[str(t.opened_at.date())].append(t.net_pnl)
    dates = sorted(daily)
    pnls = [round(sum(daily[d]), 4) for d in dates]
    return Response(pnl_bar_chart(dates, pnls), media_type="image/png")


@router.get("/charts/strategy", summary="Strategy performance bar PNG")
async def chart_strategy():
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for t in _records():
        if t.net_pnl is not None:
            groups[t.strategy].append(t.net_pnl)
    data = {s: {"net_pnl": round(sum(v), 4)} for s, v in groups.items()}
    return Response(strategy_performance_chart(data), media_type="image/png")


@router.get("/charts/pairs", summary="Pair performance bar PNG")
async def chart_pairs():
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for t in _records():
        if t.net_pnl is not None:
            groups[t.asset].append(t.net_pnl)
    data = {s: {"net_pnl": round(sum(v), 4)} for s, v in groups.items()}
    return Response(pair_performance_chart(data), media_type="image/png")


@router.get("/charts/hourly", summary="Hourly P&L heatmap PNG")
async def chart_hourly():
    from collections import defaultdict
    hourly: dict = defaultdict(list)
    for t in _records():
        if t.net_pnl is not None:
            hourly[str(t.opened_at.hour)].append(t.net_pnl)
    data = {h: {"net_pnl": round(sum(v), 4)} for h, v in hourly.items()}
    return Response(hourly_heatmap(data), media_type="image/png")


@router.get("/charts/rr", summary="R:R distribution histogram PNG")
async def chart_rr():
    vals = [t.risk_reward_ratio for t in _records() if t.risk_reward_ratio]
    return Response(rr_distribution_chart(vals), media_type="image/png")


# ─── Notifications ─────────────────────────────────────────────────────────────

@router.post("/notify/telegram/daily", summary="Send daily Telegram report")
async def notify_tg_daily(d: str = Query(..., description="YYYY-MM-DD")):
    r = generate_daily_report(_records(), _parse_date(d))
    sent = await send_telegram_report(format_daily_telegram(_daily_dict(r)))
    return {"sent": sent}


@router.post("/notify/telegram/trade/{trade_id}", summary="Send single trade alert to Telegram")
async def notify_tg_trade(trade_id: str):
    report = asdict(generate_trade_report(_find(trade_id)))
    sent = await send_telegram_report(format_trade_closed_telegram(report))
    return {"sent": sent}


@router.post("/notify/email/daily", summary="Send daily email report with PDF attachment")
async def notify_email_daily(d: str = Query(..., description="YYYY-MM-DD")):
    r = generate_daily_report(_records(), _parse_date(d))
    summary = _daily_dict(r)
    sent = await send_email_report(
        subject=f"Daily Trading Report — {d}",
        body_html=build_daily_email_html(summary),
        attachment=export_daily_pdf(summary),
        attachment_name=f"daily_report_{d}.pdf",
    )
    return {"sent": sent}


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _find(trade_id: str) -> TradeRecord:
    record = next((t for t in _records() if str(t.id) == trade_id), None)
    if not record:
        raise HTTPException(404, f"Trade {trade_id!r} not found")
    return record


def _parse_date(d: str) -> date:
    try:
        return date.fromisoformat(d)
    except ValueError:
        raise HTTPException(400, "Invalid date — use YYYY-MM-DD")


def _daily_dict(r) -> dict:
    return {
        "date": str(r.date),
        "total_trades": r.total_trades,
        "winning_trades": r.winning_trades,
        "losing_trades": r.losing_trades,
        "win_rate": r.win_rate,
        "gross_profit": r.gross_profit,
        "gross_loss": r.gross_loss,
        "net_pnl": r.net_pnl,
        "fees_paid": r.fees_paid,
        "best_trade_id": r.best_trade_id,
        "worst_trade_id": r.worst_trade_id,
        "best_trade_pnl": r.best_trade_pnl,
        "worst_trade_pnl": r.worst_trade_pnl,
        "max_drawdown": r.max_drawdown,
        "avg_win": r.avg_win,
        "avg_loss": r.avg_loss,
        "avg_rr": r.avg_rr,
        "profit_factor": r.profit_factor,
        "mistakes_count": r.mistakes_count,
        "recommendations": r.recommendations,
    }
