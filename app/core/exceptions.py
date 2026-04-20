class TradingSystemError(Exception):
    """Base exception for all trading system errors."""


class BrokerConnectionError(TradingSystemError):
    """Failed to connect to broker/exchange."""


class InsufficientFundsError(TradingSystemError):
    """Not enough balance to place order."""


class RiskLimitBreached(TradingSystemError):
    """Trade rejected due to risk rule violation."""


class KillSwitchTriggered(TradingSystemError):
    """Emergency stop activated — all trading halted."""


class SignalError(TradingSystemError):
    """Error generating trade signal."""


class OrderExecutionError(TradingSystemError):
    """Order placement or cancellation failed."""


class DataIngestionError(TradingSystemError):
    """Market data fetch failed."""


class BacktestError(TradingSystemError):
    """Backtesting engine error."""
