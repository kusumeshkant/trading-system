from dataclasses import dataclass
from app.config.settings import get_settings
from app.core.exceptions import RiskLimitBreached, KillSwitchTriggered
from app.core.logger import logger

settings = get_settings()


@dataclass
class RiskContext:
    capital: float
    daily_loss: float        # running P&L today (negative = loss)
    open_trades: int
    proposed_size: float     # position size in quote currency
    leverage: int


class RiskEngine:
    """All trade proposals must pass through here before execution."""

    def __init__(self) -> None:
        self._kill_switch_active = False

    def activate_kill_switch(self, reason: str) -> None:
        self._kill_switch_active = True
        logger.warning("kill_switch_activated", reason=reason)

    def deactivate_kill_switch(self) -> None:
        self._kill_switch_active = False
        logger.info("kill_switch_deactivated")

    @property
    def is_halted(self) -> bool:
        return self._kill_switch_active

    def validate(self, ctx: RiskContext) -> None:
        """Raises if trade should not proceed."""
        if self._kill_switch_active:
            raise KillSwitchTriggered("Kill switch is active. No trading allowed.")

        # Daily loss limit
        daily_loss_pct = abs(ctx.daily_loss) / ctx.capital * 100
        if ctx.daily_loss < 0 and daily_loss_pct >= settings.max_daily_loss_percent:
            self.activate_kill_switch(f"Daily loss limit {settings.max_daily_loss_percent}% breached")
            raise RiskLimitBreached(
                f"Daily loss {daily_loss_pct:.2f}% exceeds limit {settings.max_daily_loss_percent}%"
            )

        # Max open trades
        if ctx.open_trades >= settings.max_open_trades:
            raise RiskLimitBreached(
                f"Max open trades ({settings.max_open_trades}) reached"
            )

        # Position size limit
        max_position = ctx.capital * (settings.max_position_size_percent / 100)
        if ctx.proposed_size > max_position:
            raise RiskLimitBreached(
                f"Position size {ctx.proposed_size} exceeds max {max_position:.2f}"
            )

        # Leverage limit
        if ctx.leverage > settings.default_leverage:
            raise RiskLimitBreached(
                f"Leverage {ctx.leverage}x exceeds max {settings.default_leverage}x"
            )

        logger.info("risk_check_passed", capital=ctx.capital, open_trades=ctx.open_trades)

    def calculate_position_size(
        self,
        capital: float,
        risk_percent: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """Kelly-lite: risk only risk_percent of capital per trade."""
        risk_amount = capital * (risk_percent / 100)
        price_risk = abs(entry_price - stop_loss_price)
        if price_risk == 0:
            return 0.0
        quantity = risk_amount / price_risk
        return round(quantity, 6)
