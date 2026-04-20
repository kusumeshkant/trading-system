from dataclasses import dataclass
from typing import Optional
from app.analytics.models import TradeRecord
from app.analytics.calculator import (
    calculate_gross_pnl,
    calculate_net_pnl,
    calculate_risk_reward,
    calculate_duration_minutes,
)


@dataclass
class TradeReportData:
    trade_id: str
    datetime: str
    asset: str
    strategy: str
    trade_type: str
    entry_price: float
    exit_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    quantity: float
    fees_paid: float
    slippage: float
    gross_pnl: Optional[float]
    net_pnl: Optional[float]
    pnl_percent: Optional[float]
    risk_reward_ratio: Optional[float]
    trade_duration: str
    signal_reason: Optional[str]
    exit_reason: Optional[str]
    market_condition: Optional[str]
    screenshot_url: Optional[str]
    notes: Optional[str]
    emotions: Optional[str]
    mistakes: Optional[str]
    broker: Optional[str]
    mode: str


def generate_trade_report(record: TradeRecord) -> TradeReportData:
    gross = net = pnl_pct = None

    if record.exit_price is not None:
        gross = calculate_gross_pnl(
            record.entry_price,
            record.exit_price,
            record.quantity,
            record.trade_type.value,
        )
        net = calculate_net_pnl(gross, record.fees_paid, record.slippage)
        if record.entry_price:
            pnl_pct = round((gross / (record.entry_price * record.quantity)) * 100, 4)

    rr = calculate_risk_reward(
        record.entry_price,
        record.stop_loss,
        record.take_profit,
        record.trade_type.value,
    )

    duration = ""
    if record.closed_at and record.opened_at:
        mins = calculate_duration_minutes(record.opened_at, record.closed_at)
        h, m = divmod(int(mins), 60)
        duration = f"{h}h {m}m" if h else f"{m}m"

    return TradeReportData(
        trade_id=str(record.id),
        datetime=record.opened_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        asset=record.asset,
        strategy=record.strategy,
        trade_type=record.trade_type.value.upper(),
        entry_price=record.entry_price,
        exit_price=record.exit_price,
        stop_loss=record.stop_loss,
        take_profit=record.take_profit,
        quantity=record.quantity,
        fees_paid=record.fees_paid,
        slippage=record.slippage,
        gross_pnl=round(gross, 6) if gross is not None else None,
        net_pnl=round(net, 6) if net is not None else None,
        pnl_percent=pnl_pct,
        risk_reward_ratio=rr,
        trade_duration=duration or "Open",
        signal_reason=record.signal_reason,
        exit_reason=record.exit_reason.value if record.exit_reason else None,
        market_condition=record.market_condition.value if record.market_condition else None,
        screenshot_url=record.screenshot_url,
        notes=record.notes,
        emotions=record.emotions,
        mistakes=record.mistakes,
        broker=record.broker,
        mode=record.mode,
    )
