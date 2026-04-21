"""
Binance CSV import — supports Spot Trade History and Futures Trade History exports.
"""
import csv
import io
import uuid
from datetime import datetime
from typing import List, Tuple
from app.analytics.models import TradeRecord, TradeType


_SPOT_DT_FMTS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M:%S")


def _parse_dt(s: str) -> datetime:
    s = s.strip()
    for fmt in _SPOT_DT_FMTS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date format: {s!r}")


def _safe_float(s: str) -> float:
    try:
        return float(str(s).strip().replace(",", "") or 0)
    except (ValueError, TypeError):
        return 0.0


def parse_binance_csv(content: str) -> Tuple[List[TradeRecord], List[str]]:
    """
    Auto-detects Binance CSV format and returns (records, error_messages).

    Supported formats
    -----------------
    Spot Trade History:
        Date(UTC), Pair, Side, Order Price, Order Amount,
        AvgTrading Price, Filled, Total, status

    Futures Trade History:
        Time, Symbol, Side, Price, Quantity, Fee, Realized Profit
    """
    reader = csv.DictReader(io.StringIO(content.strip()))
    fieldnames = [f.strip() for f in (reader.fieldnames or [])]

    if not fieldnames:
        return [], ["Empty or unreadable CSV"]

    if "Date(UTC)" in fieldnames:
        return _parse_spot(reader)
    if "Time" in fieldnames and "Symbol" in fieldnames:
        return _parse_futures(reader)

    return [], [
        f"Unrecognised CSV format. Expected columns: 'Date(UTC)' (spot) "
        f"or 'Time'+'Symbol' (futures). Found: {fieldnames[:8]}"
    ]


# ── Spot ──────────────────────────────────────────────────────────────────────

def _parse_spot(reader: csv.DictReader) -> Tuple[List[TradeRecord], List[str]]:
    errors: List[str] = []
    open_buys: dict = {}   # pair → trade dict
    records: List[TradeRecord] = []

    for i, raw in enumerate(reader, 2):
        row = {k.strip(): (v or "").strip() for k, v in raw.items()}
        try:
            status = row.get("status", "FILLED").upper()
            if status not in ("FILLED", ""):
                continue

            pair = row.get("Pair", "").upper()
            side = row.get("Side", "").upper()
            dt = _parse_dt(row.get("Date(UTC)", ""))
            price = _safe_float(row.get("AvgTrading Price") or row.get("Order Price", "0"))
            qty = _safe_float(row.get("Filled") or row.get("Order Amount", "0"))

            if not pair or price <= 0 or qty <= 0:
                errors.append(f"Row {i}: skipped — missing pair/price/qty")
                continue

            if side == "BUY":
                open_buys[pair] = {"dt": dt, "price": price, "qty": qty}

            elif side == "SELL":
                if pair in open_buys:
                    buy = open_buys.pop(pair)
                    records.append(_make_trade(
                        asset=pair, side="long",
                        opened_at=buy["dt"], closed_at=dt,
                        entry=buy["price"], exit_p=price,
                        qty=min(buy["qty"], qty),
                    ))
                else:
                    records.append(_make_trade(
                        asset=pair, side="short",
                        opened_at=dt, entry=price, qty=qty,
                    ))
        except Exception as exc:
            errors.append(f"Row {i}: {exc}")

    # Remaining unmatched BUYs → open long positions
    for pair, buy in open_buys.items():
        records.append(_make_trade(
            asset=pair, side="long",
            opened_at=buy["dt"], entry=buy["price"], qty=buy["qty"],
        ))

    return records, errors


# ── Futures ───────────────────────────────────────────────────────────────────

def _parse_futures(reader: csv.DictReader) -> Tuple[List[TradeRecord], List[str]]:
    errors: List[str] = []
    records: List[TradeRecord] = []

    for i, raw in enumerate(reader, 2):
        row = {k.strip(): (v or "").strip() for k, v in raw.items()}
        try:
            dt = _parse_dt(row.get("Time", ""))
            symbol = row.get("Symbol", "").upper()
            side = row.get("Side", "").upper()
            price = _safe_float(row.get("Price", "0"))
            qty = _safe_float(row.get("Quantity", "0"))
            fee = _safe_float(row.get("Fee", "0"))
            realized = _safe_float(row.get("Realized Profit", "0"))

            if not symbol or price <= 0:
                errors.append(f"Row {i}: skipped — missing symbol or price")
                continue

            trade_type = TradeType.LONG if side == "BUY" else TradeType.SHORT
            net_pnl = realized if realized != 0 else None
            gross_pnl = (realized + fee) if realized != 0 else None

            records.append(TradeRecord(
                id=uuid.uuid4(),
                asset=symbol,
                strategy="Binance Futures Import",
                trade_type=trade_type,
                opened_at=dt,
                entry_price=price,
                quantity=qty,
                fees_paid=fee,
                gross_pnl=round(gross_pnl, 6) if gross_pnl is not None else None,
                net_pnl=round(net_pnl, 6) if net_pnl is not None else None,
                mode="live",
                broker="Binance",
            ))
        except Exception as exc:
            errors.append(f"Row {i}: {exc}")

    return records, errors


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_trade(
    asset: str, side: str,
    opened_at: datetime,
    entry: float, qty: float,
    closed_at: datetime = None,
    exit_p: float = None,
) -> TradeRecord:
    trade_type = TradeType.LONG if side == "long" else TradeType.SHORT
    gross = None
    net = None
    duration = None

    if exit_p is not None:
        if side == "long":
            gross = (exit_p - entry) * qty
        else:
            gross = (entry - exit_p) * qty
        gross = round(gross, 6)
        net = round(gross, 6)

    if closed_at and opened_at:
        duration = round((closed_at - opened_at).total_seconds() / 60, 2)

    return TradeRecord(
        id=uuid.uuid4(),
        asset=asset,
        strategy="Binance Spot Import",
        trade_type=trade_type,
        opened_at=opened_at,
        closed_at=closed_at,
        entry_price=entry,
        exit_price=exit_p,
        quantity=qty,
        gross_pnl=gross,
        net_pnl=net,
        trade_duration_minutes=duration,
        mode="live",
        broker="Binance",
    )
