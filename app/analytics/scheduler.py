from datetime import date, timedelta
from typing import Callable, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.logger import logger


def setup_analytics_scheduler(get_trades: Callable) -> AsyncIOScheduler:
    """
    Register daily/weekly auto-report jobs.
    get_trades: zero-arg callable returning current List[TradeRecord].
    """
    scheduler = AsyncIOScheduler()

    @scheduler.scheduled_job(CronTrigger(hour=23, minute=55), id="daily_report")
    async def _daily():
        from app.analytics.reports.daily_report import generate_daily_report
        from app.analytics.exporters.pdf_exporter import export_daily_pdf
        from app.analytics.notifications.telegram_sender import (
            send_telegram_report, format_daily_telegram,
        )
        from app.analytics.notifications.email_sender import (
            send_email_report, build_daily_email_html,
        )

        today = date.today()
        trades = get_trades()
        report = generate_daily_report(trades, today)

        summary = _daily_to_dict(report)
        await send_telegram_report(format_daily_telegram(summary))
        await send_email_report(
            subject=f"Daily Trading Report — {today}",
            body_html=build_daily_email_html(summary),
            attachment=export_daily_pdf(summary),
            attachment_name=f"daily_report_{today}.pdf",
        )
        logger.info("daily_report_dispatched", date=str(today), trades=report.total_trades)

    @scheduler.scheduled_job(CronTrigger(day_of_week="sun", hour=23, minute=50), id="weekly_report")
    async def _weekly():
        from app.analytics.reports.periodic_report import generate_weekly_report
        from app.analytics.notifications.telegram_sender import (
            send_telegram_report, format_weekly_telegram,
        )

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        trades = get_trades()
        report = generate_weekly_report(trades, week_start, today)

        summary = {
            "week_start": str(report.week_start),
            "week_end": str(report.week_end),
            "total_trades": report.total_trades,
            "win_rate": report.win_rate,
            "net_pnl": report.net_pnl,
            "avg_rr": report.avg_rr,
            "max_drawdown": report.max_drawdown,
            "max_consecutive_wins": report.max_consecutive_wins,
            "max_consecutive_losses": report.max_consecutive_losses,
            "strategy_breakdown": report.strategy_breakdown,
            "improvement_suggestions": report.improvement_suggestions,
        }
        await send_telegram_report(format_weekly_telegram(summary))
        logger.info("weekly_report_dispatched", week_start=str(week_start))

    scheduler.start()
    return scheduler


def _daily_to_dict(report) -> dict:
    return {
        "date": str(report.date),
        "total_trades": report.total_trades,
        "winning_trades": report.winning_trades,
        "losing_trades": report.losing_trades,
        "win_rate": report.win_rate,
        "gross_profit": report.gross_profit,
        "gross_loss": report.gross_loss,
        "net_pnl": report.net_pnl,
        "fees_paid": report.fees_paid,
        "max_drawdown": report.max_drawdown,
        "avg_win": report.avg_win,
        "avg_loss": report.avg_loss,
        "avg_rr": report.avg_rr,
        "profit_factor": report.profit_factor,
        "mistakes_count": report.mistakes_count,
        "recommendations": report.recommendations,
    }
