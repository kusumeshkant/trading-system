"""Add analytics tables: trade_records, daily_reports, weekly_reports, monthly_reports

Revision ID: 002
Revises: 001
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "002"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "trade_records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("trade_id", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("opened_at", sa.DateTime, nullable=False),
        sa.Column("closed_at", sa.DateTime, nullable=True),
        sa.Column("asset", sa.String, nullable=False),
        sa.Column("strategy", sa.String, nullable=False),
        sa.Column("trade_type", sa.Enum("long", "short", "buy", "sell", name="tradetype"), nullable=False),
        sa.Column("entry_price", sa.Float, nullable=False),
        sa.Column("exit_price", sa.Float, nullable=True),
        sa.Column("stop_loss", sa.Float, nullable=True),
        sa.Column("take_profit", sa.Float, nullable=True),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("fees_paid", sa.Float, server_default="0"),
        sa.Column("slippage", sa.Float, server_default="0"),
        sa.Column("gross_pnl", sa.Float, nullable=True),
        sa.Column("net_pnl", sa.Float, nullable=True),
        sa.Column("pnl_percent", sa.Float, nullable=True),
        sa.Column("risk_reward_ratio", sa.Float, nullable=True),
        sa.Column("trade_duration_minutes", sa.Float, nullable=True),
        sa.Column("signal_reason", sa.Text, nullable=True),
        sa.Column("exit_reason", sa.Enum(
            "take_profit", "stop_loss", "manual", "trailing_stop", "time_exit", "signal_reversal",
            name="exitreason",
        ), nullable=True),
        sa.Column("market_condition", sa.Enum(
            "trending_up", "trending_down", "ranging", "high_volatility", "low_volatility",
            name="marketcondition",
        ), nullable=True),
        sa.Column("screenshot_url", sa.String, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("emotions", sa.String, nullable=True),
        sa.Column("mistakes", sa.Text, nullable=True),
        sa.Column("tags", JSON, nullable=True),
        sa.Column("broker", sa.String, nullable=True),
        sa.Column("mode", sa.String, server_default="paper"),
    )

    op.create_table(
        "daily_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date, unique=True, nullable=False),
        sa.Column("generated_at", sa.DateTime, nullable=True),
        sa.Column("total_trades", sa.Integer, server_default="0"),
        sa.Column("winning_trades", sa.Integer, server_default="0"),
        sa.Column("losing_trades", sa.Integer, server_default="0"),
        sa.Column("win_rate", sa.Float, server_default="0"),
        sa.Column("gross_profit", sa.Float, server_default="0"),
        sa.Column("gross_loss", sa.Float, server_default="0"),
        sa.Column("net_pnl", sa.Float, server_default="0"),
        sa.Column("fees_paid", sa.Float, server_default="0"),
        sa.Column("best_trade_id", sa.String, nullable=True),
        sa.Column("worst_trade_id", sa.String, nullable=True),
        sa.Column("best_trade_pnl", sa.Float, nullable=True),
        sa.Column("worst_trade_pnl", sa.Float, nullable=True),
        sa.Column("max_drawdown", sa.Float, server_default="0"),
        sa.Column("avg_win", sa.Float, server_default="0"),
        sa.Column("avg_loss", sa.Float, server_default="0"),
        sa.Column("avg_rr", sa.Float, server_default="0"),
        sa.Column("profit_factor", sa.Float, server_default="0"),
        sa.Column("mistakes_count", sa.Integer, server_default="0"),
        sa.Column("recommendations", JSON, nullable=True),
    )

    op.create_table(
        "weekly_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("week_start", sa.Date, nullable=False),
        sa.Column("week_end", sa.Date, nullable=False),
        sa.Column("generated_at", sa.DateTime, nullable=True),
        sa.Column("total_trades", sa.Integer, server_default="0"),
        sa.Column("win_rate", sa.Float, server_default="0"),
        sa.Column("net_pnl", sa.Float, server_default="0"),
        sa.Column("avg_rr", sa.Float, server_default="0"),
        sa.Column("max_drawdown", sa.Float, server_default="0"),
        sa.Column("profit_factor", sa.Float, server_default="0"),
        sa.Column("max_consecutive_wins", sa.Integer, server_default="0"),
        sa.Column("max_consecutive_losses", sa.Integer, server_default="0"),
        sa.Column("strategy_breakdown", JSON, nullable=True),
        sa.Column("pair_breakdown", JSON, nullable=True),
        sa.Column("hourly_breakdown", JSON, nullable=True),
        sa.Column("equity_curve", JSON, nullable=True),
        sa.Column("improvement_suggestions", JSON, nullable=True),
    )

    op.create_table(
        "monthly_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column("generated_at", sa.DateTime, nullable=True),
        sa.Column("total_trades", sa.Integer, server_default="0"),
        sa.Column("win_rate", sa.Float, server_default="0"),
        sa.Column("net_pnl", sa.Float, server_default="0"),
        sa.Column("avg_rr", sa.Float, server_default="0"),
        sa.Column("max_drawdown", sa.Float, server_default="0"),
        sa.Column("profit_factor", sa.Float, server_default="0"),
        sa.Column("sharpe_ratio", sa.Float, nullable=True),
        sa.Column("strategy_breakdown", JSON, nullable=True),
        sa.Column("pair_breakdown", JSON, nullable=True),
        sa.Column("hourly_breakdown", JSON, nullable=True),
        sa.Column("loss_patterns", JSON, nullable=True),
        sa.Column("equity_curve", JSON, nullable=True),
        sa.Column("improvement_suggestions", JSON, nullable=True),
    )

    op.create_index("ix_trade_records_asset", "trade_records", ["asset"])
    op.create_index("ix_trade_records_strategy", "trade_records", ["strategy"])
    op.create_index("ix_trade_records_opened_at", "trade_records", ["opened_at"])
    op.create_index("ix_trade_records_closed_at", "trade_records", ["closed_at"])
    op.create_index("ix_daily_reports_date", "daily_reports", ["date"])


def downgrade():
    op.drop_table("monthly_reports")
    op.drop_table("weekly_reports")
    op.drop_table("daily_reports")
    op.drop_table("trade_records")
    op.execute("DROP TYPE IF EXISTS tradetype")
    op.execute("DROP TYPE IF EXISTS exitreason")
    op.execute("DROP TYPE IF EXISTS marketcondition")
