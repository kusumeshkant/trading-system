from app.config.settings import get_settings
from app.core.logger import logger


async def send_telegram_report(message: str, parse_mode: str = "HTML") -> bool:
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("telegram_not_configured")
        return False
    try:
        from telegram import Bot
        bot = Bot(token=settings.telegram_bot_token)
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=message,
            parse_mode=parse_mode,
        )
        return True
    except Exception as e:
        logger.error("telegram_send_failed", error=str(e))
        return False


def format_daily_telegram(summary: dict) -> str:
    pnl = summary.get("net_pnl", 0)
    bullet = "🟢" if pnl >= 0 else "🔴"
    recs = summary.get("recommendations", [])
    rec_line = f"\n\n💡 <i>{recs[0]}</i>" if recs else ""
    return (
        f"{bullet} <b>Daily Report — {summary.get('date', '')}</b>\n\n"
        f"📊 Trades: {summary.get('total_trades', 0)}"
        f" ({summary.get('winning_trades', 0)}W / {summary.get('losing_trades', 0)}L)\n"
        f"🎯 Win Rate: {summary.get('win_rate', 0):.1f}%\n"
        f"💰 Net P&L: <b>${pnl:+,.4f}</b>\n"
        f"📉 Max DD: ${summary.get('max_drawdown', 0):,.4f}\n"
        f"⚖️ Avg R:R: 1:{summary.get('avg_rr', 0):.2f}\n"
        f"📈 Profit Factor: {summary.get('profit_factor', 0):.2f}\n"
        f"⚠️ Mistakes: {summary.get('mistakes_count', 0)}"
        f"{rec_line}"
    )


def format_trade_closed_telegram(report: dict) -> str:
    pnl = report.get("net_pnl") or 0
    bullet = "🟢" if pnl >= 0 else "🔴"
    return (
        f"{bullet} <b>Trade Closed — {report.get('asset', '')}</b>\n\n"
        f"📋 Strategy: {report.get('strategy', '—')}\n"
        f"🔄 Type: {report.get('trade_type', '').upper()}\n"
        f"🎯 Entry: ${report.get('entry_price', 0):,.6f}\n"
        f"🏁 Exit: ${report.get('exit_price', 0):,.6f}\n"
        f"💰 Net P&L: <b>${pnl:+,.4f}</b>\n"
        f"⚖️ R:R: 1:{report.get('risk_reward_ratio', '—')}\n"
        f"⏱ Duration: {report.get('trade_duration', '—')}\n"
        f"📌 Exit: {report.get('exit_reason', '—')}"
    )


def format_weekly_telegram(report: dict) -> str:
    pnl = report.get("net_pnl", 0)
    bullet = "🟢" if pnl >= 0 else "🔴"
    best_strat = max(
        report.get("strategy_breakdown", {}).items(),
        key=lambda x: x[1].get("net_pnl", 0),
        default=("—", {}),
    )[0]
    recs = report.get("improvement_suggestions", [])
    rec_lines = "\n".join(f"💡 {r}" for r in recs[:3])
    return (
        f"{bullet} <b>Weekly Report ({report.get('week_start')} → {report.get('week_end')})</b>\n\n"
        f"📊 Trades: {report.get('total_trades', 0)}\n"
        f"🎯 Win Rate: {report.get('win_rate', 0):.1f}%\n"
        f"💰 Net P&L: <b>${pnl:+,.4f}</b>\n"
        f"📉 Max DD: ${report.get('max_drawdown', 0):,.4f}\n"
        f"⚖️ Avg R:R: 1:{report.get('avg_rr', 0):.2f}\n"
        f"🔥 Best Strategy: {best_strat}\n"
        f"🏆 Max Win Streak: {report.get('max_consecutive_wins', 0)}\n"
        f"💀 Max Loss Streak: {report.get('max_consecutive_losses', 0)}\n\n"
        f"{rec_lines}"
    )
