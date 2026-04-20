from sqlalchemy import Column, String, Float, DateTime, Enum, Integer, Text, Date, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
import enum

Base = declarative_base()


class TradeType(str, enum.Enum):
    LONG = "long"
    SHORT = "short"
    BUY = "buy"
    SELL = "sell"


class ExitReason(str, enum.Enum):
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    MANUAL = "manual"
    TRAILING_STOP = "trailing_stop"
    TIME_EXIT = "time_exit"
    SIGNAL_REVERSAL = "signal_reversal"


class MarketCondition(str, enum.Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


class TradeRecord(Base):
    __tablename__ = "trade_records"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Time & asset
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    asset = Column(String, nullable=False)
    strategy = Column(String, nullable=False)
    trade_type = Column(Enum(TradeType), nullable=False)

    # Prices & sizing
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)

    # Costs
    fees_paid = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)

    # P&L (auto-calculated on record creation)
    gross_pnl = Column(Float, nullable=True)
    net_pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)

    # Risk metrics
    risk_reward_ratio = Column(Float, nullable=True)
    trade_duration_minutes = Column(Float, nullable=True)

    # Context
    signal_reason = Column(Text, nullable=True)
    exit_reason = Column(Enum(ExitReason), nullable=True)
    market_condition = Column(Enum(MarketCondition), nullable=True)

    # Journal
    screenshot_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    emotions = Column(String, nullable=True)
    mistakes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)

    # Meta
    broker = Column(String, nullable=True)
    mode = Column(String, default="paper")


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, unique=True, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)

    gross_profit = Column(Float, default=0.0)
    gross_loss = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    fees_paid = Column(Float, default=0.0)

    best_trade_id = Column(String, nullable=True)
    worst_trade_id = Column(String, nullable=True)
    best_trade_pnl = Column(Float, nullable=True)
    worst_trade_pnl = Column(Float, nullable=True)

    max_drawdown = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    avg_rr = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)

    mistakes_count = Column(Integer, default=0)
    recommendations = Column(JSON, nullable=True)


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    avg_rr = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)

    max_consecutive_wins = Column(Integer, default=0)
    max_consecutive_losses = Column(Integer, default=0)

    strategy_breakdown = Column(JSON, nullable=True)
    pair_breakdown = Column(JSON, nullable=True)
    hourly_breakdown = Column(JSON, nullable=True)
    equity_curve = Column(JSON, nullable=True)
    improvement_suggestions = Column(JSON, nullable=True)


class MonthlyReport(Base):
    __tablename__ = "monthly_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    avg_rr = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)

    strategy_breakdown = Column(JSON, nullable=True)
    pair_breakdown = Column(JSON, nullable=True)
    hourly_breakdown = Column(JSON, nullable=True)
    loss_patterns = Column(JSON, nullable=True)
    equity_curve = Column(JSON, nullable=True)
    improvement_suggestions = Column(JSON, nullable=True)
