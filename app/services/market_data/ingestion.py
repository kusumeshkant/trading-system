import pandas as pd
from app.brokers.binance.client import BinanceClient
from app.core.exceptions import DataIngestionError
from app.core.logger import logger


class MarketDataService:
    def __init__(self, broker: BinanceClient) -> None:
        self._broker = broker

    async def get_ohlcv(self, symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
        """Fetch OHLCV from broker and return clean DataFrame."""
        try:
            raw = await self._broker.get_klines(symbol, interval, limit)
            df = pd.DataFrame(raw, columns=[
                "timestamp", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades",
                "taker_base", "taker_quote", "ignore",
            ])
            df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
            df.set_index("timestamp", inplace=True)
            df.attrs["symbol"] = symbol
            logger.info("market_data_fetched", symbol=symbol, interval=interval, rows=len(df))
            return df
        except Exception as e:
            raise DataIngestionError(f"Failed to ingest {symbol}: {e}") from e

    async def get_current_price(self, symbol: str) -> float:
        """Latest close price."""
        df = await self.get_ohlcv(symbol, "1m", limit=2)
        return float(df["close"].iloc[-1])
