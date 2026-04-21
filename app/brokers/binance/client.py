import asyncio
from typing import Optional
from binance import AsyncClient
from binance.exceptions import BinanceAPIException
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config.settings import get_settings
from app.core.exceptions import BrokerConnectionError, OrderExecutionError, InsufficientFundsError
from app.core.logger import logger

settings = get_settings()


class BinanceClient:
    def __init__(self) -> None:
        self._client: Optional[AsyncClient] = None

    async def connect(self) -> None:
        try:
            self._client = await AsyncClient.create(
                api_key=settings.binance_api_key,
                api_secret=settings.binance_api_secret,
                testnet=settings.binance_testnet,
            )
            logger.info("binance_connected", testnet=settings.binance_testnet)
        except Exception as e:
            raise BrokerConnectionError(f"Binance connection failed: {e}") from e

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close_connection()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_klines(self, symbol: str, interval: str, limit: int = 200) -> list:
        """Fetch OHLCV candlestick data."""
        try:
            return await self._client.get_klines(
                symbol=symbol, interval=interval, limit=limit
            )
        except BinanceAPIException as e:
            raise BrokerConnectionError(f"Failed to fetch klines: {e}") from e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_balance(self, asset: str = "USDT") -> float:
        """Get available balance for an asset."""
        try:
            account = await self._client.get_account()
            for balance in account["balances"]:
                if balance["asset"] == asset:
                    return float(balance["free"])
            return 0.0
        except BinanceAPIException as e:
            raise BrokerConnectionError(f"Failed to fetch balance: {e}") from e

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=5))
    async def place_market_order(
        self,
        symbol: str,
        side: str,       # "BUY" | "SELL"
        quantity: float,
    ) -> dict:
        """Place a market order. Returns order response."""
        try:
            order = await self._client.create_order(
                symbol=symbol,
                side=side.upper(),
                type="MARKET",
                quantity=quantity,
            )
            logger.info("order_placed", symbol=symbol, side=side, quantity=quantity, order_id=order["orderId"])
            return order
        except BinanceAPIException as e:
            if "insufficient balance" in str(e).lower():
                raise InsufficientFundsError(str(e)) from e
            raise OrderExecutionError(f"Order failed: {e}") from e

    async def place_oco_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_loss: float,
        take_profit: float,
    ) -> dict:
        """Place OCO (One-Cancels-Other) order for SL + TP simultaneously."""
        try:
            order = await self._client.create_oco_order(
                symbol=symbol,
                side=side.upper(),
                quantity=quantity,
                price=str(take_profit),
                stopPrice=str(stop_loss),
                stopLimitPrice=str(stop_loss * 0.999),  # 0.1% slippage buffer
                stopLimitTimeInForce="GTC",
            )
            logger.info("oco_order_placed", symbol=symbol, sl=stop_loss, tp=take_profit)
            return order
        except BinanceAPIException as e:
            raise OrderExecutionError(f"OCO order failed: {e}") from e

    async def get_open_orders(self, symbol: Optional[str] = None) -> list:
        try:
            return await self._client.get_open_orders(symbol=symbol)
        except BinanceAPIException as e:
            raise BrokerConnectionError(str(e)) from e

    async def cancel_all_orders(self, symbol: str) -> None:
        try:
            await self._client.cancel_open_orders(symbol=symbol)
            logger.warning("all_orders_cancelled", symbol=symbol)
        except BinanceAPIException as e:
            raise OrderExecutionError(str(e)) from e
