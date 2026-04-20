from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal
from app.services.market_data.ingestion import MarketDataService
from app.services.signals.engine import SignalEngine
from app.services.orders.executor import OrderExecutor
from app.risk.engine import RiskEngine
from app.core.logger import logger

router = APIRouter(prefix="/trading", tags=["trading"])


class TradeRequest(BaseModel):
    symbol: str = "BTCUSDT"
    interval: str = "1h"
    mode: Literal["paper", "live"] = "paper"
    risk_percent: float = 1.0
    capital: float
    daily_loss: float = 0.0
    open_trades: int = 0


class KillSwitchRequest(BaseModel):
    activate: bool
    reason: str = "Manual trigger"


_risk_engine = RiskEngine()


@router.post("/signal")
async def get_signal(req: TradeRequest):
    """Analyze market and return signal without executing."""
    from app.brokers.binance.client import BinanceClient
    from app.strategies.implementations.ema_crossover import EMACrossoverStrategy
    from app.strategies.implementations.rsi_mean_reversion import RSIMeanReversionStrategy

    broker = BinanceClient()
    await broker.connect()

    try:
        data_svc = MarketDataService(broker)
        df = await data_svc.get_ohlcv(req.symbol, req.interval)

        signal_engine = SignalEngine([
            EMACrossoverStrategy(),
            RSIMeanReversionStrategy(),
        ])
        signal = signal_engine.best_signal(df)

        if not signal:
            return {"signal": "none", "reason": "No strategy triggered"}

        return {"signal": signal}
    finally:
        await broker.disconnect()


@router.post("/execute")
async def execute_trade(req: TradeRequest):
    """Generate signal and execute if valid."""
    from app.brokers.binance.client import BinanceClient
    from app.strategies.implementations.ema_crossover import EMACrossoverStrategy
    from app.strategies.implementations.rsi_mean_reversion import RSIMeanReversionStrategy

    if req.mode == "live":
        logger.warning("live_trade_requested")

    broker = BinanceClient()
    await broker.connect()

    try:
        data_svc = MarketDataService(broker)
        df = await data_svc.get_ohlcv(req.symbol, req.interval)

        signal_engine = SignalEngine([
            EMACrossoverStrategy(),
            RSIMeanReversionStrategy(),
        ])
        signal = signal_engine.best_signal(df)

        if not signal:
            return {"status": "no_signal"}

        executor = OrderExecutor(broker, _risk_engine)
        result = await executor.execute(
            signal=signal,
            capital=req.capital,
            daily_loss=req.daily_loss,
            open_trades=req.open_trades,
            risk_percent=req.risk_percent,
            mode=req.mode,
        )
        return result
    finally:
        await broker.disconnect()


@router.post("/kill-switch")
async def kill_switch(req: KillSwitchRequest):
    if req.activate:
        _risk_engine.activate_kill_switch(req.reason)
        return {"status": "activated", "reason": req.reason}
    else:
        _risk_engine.deactivate_kill_switch()
        return {"status": "deactivated"}


@router.get("/status")
async def status():
    return {
        "kill_switch": _risk_engine.is_halted,
        "app": "running",
    }
