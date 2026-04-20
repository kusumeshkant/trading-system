import asyncio
from telegram import Bot
from app.config.settings import get_settings
from app.core.logger import logger

settings = get_settings()


class TelegramAlerter:
    def __init__(self) -> None:
        self._bot = Bot(token=settings.telegram_bot_token) if settings.telegram_bot_token else None

    async def send(self, message: str) -> None:
        if not self._bot:
            logger.warning("telegram_not_configured")
            return
        try:
            await self._bot.send_message(
                chat_id=settings.telegram_chat_id,
                text=message,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error("telegram_alert_failed", error=str(e))

    async def trade_opened(self, symbol: str, side: str, entry: float, sl: float, tp: float) -> None:
        msg = (
            f"*TRADE OPENED* \n"
            f"Symbol: `{symbol}`\n"
            f"Side: `{side.upper()}`\n"
            f"Entry: `{entry}`\n"
            f"Stop Loss: `{sl}`\n"
            f"Take Profit: `{tp}`"
        )
        await self.send(msg)

    async def trade_closed(self, symbol: str, pnl: float) -> None:
        emoji = "PROFIT" if pnl >= 0 else "LOSS"
        msg = f"*TRADE CLOSED — {emoji}*\nSymbol: `{symbol}`\nPnL: `{pnl:+.2f} USDT`"
        await self.send(msg)

    async def kill_switch_alert(self, reason: str) -> None:
        msg = f"*KILL SWITCH ACTIVATED*\nReason: {reason}\nAll trading halted."
        await self.send(msg)
