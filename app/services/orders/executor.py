from app.brokers.binance.client import BinanceClient
from app.risk.engine import RiskEngine, RiskContext
from app.strategies.base.strategy import Signal
from app.core.exceptions import RiskLimitBreached, KillSwitchTriggered
from app.core.logger import logger
from app.config.settings import get_settings

settings = get_settings()


class OrderExecutor:
    def __init__(self, broker: BinanceClient, risk: RiskEngine) -> None:
        self._broker = broker
        self._risk = risk

    async def execute(
        self,
        signal: Signal,
        capital: float,
        daily_loss: float,
        open_trades: int,
        risk_percent: float = 1.0,    # risk 1% of capital per trade
        mode: str = "paper",
    ) -> dict:
        quantity = self._risk.calculate_position_size(
            capital=capital,
            risk_percent=risk_percent,
            entry_price=signal.entry_price,
            stop_loss_price=signal.stop_loss,
        )

        ctx = RiskContext(
            capital=capital,
            daily_loss=daily_loss,
            open_trades=open_trades,
            proposed_size=quantity * signal.entry_price,
            leverage=settings.default_leverage,
        )

        try:
            self._risk.validate(ctx)
        except (RiskLimitBreached, KillSwitchTriggered) as e:
            logger.warning("order_blocked_by_risk", reason=str(e))
            return {"status": "blocked", "reason": str(e)}

        if mode == "paper":
            logger.info(
                "paper_trade",
                symbol=signal.symbol,
                side=signal.side,
                entry=signal.entry_price,
                sl=signal.stop_loss,
                tp=signal.take_profit,
                qty=quantity,
            )
            return {
                "status": "paper",
                "symbol": signal.symbol,
                "side": signal.side,
                "quantity": quantity,
                "entry_price": signal.entry_price,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
            }

        # Live mode
        order = await self._broker.place_market_order(
            symbol=signal.symbol,
            side="BUY" if signal.side == "buy" else "SELL",
            quantity=quantity,
        )

        # Attach OCO for automatic SL + TP management
        exit_side = "SELL" if signal.side == "buy" else "BUY"
        await self._broker.place_oco_order(
            symbol=signal.symbol,
            side=exit_side,
            quantity=quantity,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
        )

        return {"status": "live", "order": order}
