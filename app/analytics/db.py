"""
Simple synchronous SQLite-based persistence for trade records.
Falls back to in-memory if DB is unavailable.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from app.analytics.models import TradeRecord, TradeType, ExitReason, MarketCondition

DB_PATH = Path(__file__).parent.parent.parent / "trades.db"


def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trade_records (
            id TEXT PRIMARY KEY,
            trade_id TEXT,
            created_at TEXT,
            opened_at TEXT NOT NULL,
            closed_at TEXT,
            asset TEXT NOT NULL,
            strategy TEXT NOT NULL,
            trade_type TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL,
            stop_loss REAL,
            take_profit REAL,
            quantity REAL NOT NULL,
            fees_paid REAL DEFAULT 0,
            slippage REAL DEFAULT 0,
            gross_pnl REAL,
            net_pnl REAL,
            pnl_percent REAL,
            risk_reward_ratio REAL,
            trade_duration_minutes REAL,
            signal_reason TEXT,
            exit_reason TEXT,
            market_condition TEXT,
            screenshot_url TEXT,
            notes TEXT,
            emotions TEXT,
            mistakes TEXT,
            tags TEXT,
            broker TEXT,
            mode TEXT DEFAULT 'paper'
        )
    """)
    conn.commit()
    conn.close()


def save_trade(record: TradeRecord):
    conn = _get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO trade_records VALUES (
            ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
    """, (
        str(record.id), record.trade_id,
        record.created_at.isoformat() if record.created_at else None,
        record.opened_at.isoformat(),
        record.closed_at.isoformat() if record.closed_at else None,
        record.asset, record.strategy, record.trade_type.value,
        record.entry_price, record.exit_price,
        record.stop_loss, record.take_profit, record.quantity,
        record.fees_paid, record.slippage,
        record.gross_pnl, record.net_pnl, record.pnl_percent,
        record.risk_reward_ratio, record.trade_duration_minutes,
        record.signal_reason,
        record.exit_reason.value if record.exit_reason else None,
        record.market_condition.value if record.market_condition else None,
        record.screenshot_url, record.notes, record.emotions,
        record.mistakes,
        json.dumps(record.tags) if record.tags else None,
        record.broker, record.mode,
    ))
    conn.commit()
    conn.close()


def delete_trade(trade_id: str) -> bool:
    conn = _get_conn()
    c = conn.execute("DELETE FROM trade_records WHERE id = ?", (trade_id,))
    conn.commit()
    conn.close()
    return c.rowcount > 0


def load_all_trades() -> List[TradeRecord]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM trade_records ORDER BY opened_at ASC").fetchall()
    conn.close()
    return [_row_to_record(r) for r in rows]


def _row_to_record(r) -> TradeRecord:
    def dt(s): return datetime.fromisoformat(s) if s else None
    return TradeRecord(
        id=uuid.UUID(r["id"]),
        trade_id=r["trade_id"],
        created_at=dt(r["created_at"]),
        opened_at=dt(r["opened_at"]),
        closed_at=dt(r["closed_at"]),
        asset=r["asset"],
        strategy=r["strategy"],
        trade_type=TradeType(r["trade_type"]),
        entry_price=r["entry_price"],
        exit_price=r["exit_price"],
        stop_loss=r["stop_loss"],
        take_profit=r["take_profit"],
        quantity=r["quantity"],
        fees_paid=r["fees_paid"] or 0,
        slippage=r["slippage"] or 0,
        gross_pnl=r["gross_pnl"],
        net_pnl=r["net_pnl"],
        pnl_percent=r["pnl_percent"],
        risk_reward_ratio=r["risk_reward_ratio"],
        trade_duration_minutes=r["trade_duration_minutes"],
        signal_reason=r["signal_reason"],
        exit_reason=ExitReason(r["exit_reason"]) if r["exit_reason"] else None,
        market_condition=MarketCondition(r["market_condition"]) if r["market_condition"] else None,
        screenshot_url=r["screenshot_url"],
        notes=r["notes"],
        emotions=r["emotions"],
        mistakes=r["mistakes"],
        tags=json.loads(r["tags"]) if r["tags"] else None,
        broker=r["broker"],
        mode=r["mode"] or "paper",
    )
