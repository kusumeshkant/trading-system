import io
from datetime import datetime
from typing import List, Optional, Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
)
from app.analytics.reports.trade_report import TradeReportData

_DARK = colors.HexColor("#1A1A2E")
_BLUE = colors.HexColor("#4A9EFF")
_GREEN = colors.HexColor("#D4EDDA")
_RED = colors.HexColor("#F8D7DA")
_ALT = colors.HexColor("#F0F4FF")
_THIN = colors.HexColor("#CCCCCC")

_BASE_TABLE_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), _DARK),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, 0), 10),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_ALT, colors.white]),
    ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
    ("FONTSIZE", (0, 1), (-1, -1), 9),
    ("GRID", (0, 0), (-1, -1), 0.5, _THIN),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
])


def _make_doc(buffer) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
    )


def _header(title: str, subtitle: str = "") -> list:
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        textColor=_DARK, fontSize=20, spaceAfter=4,
    )
    elements = [Paragraph(title, title_style)]
    if subtitle:
        elements.append(Paragraph(subtitle, styles["Normal"]))
    elements += [
        Spacer(1, 0.15 * inch),
        HRFlowable(width="100%", thickness=2, color=_BLUE),
        Spacer(1, 0.2 * inch),
    ]
    return elements


def _footer_text() -> list:
    styles = getSampleStyleSheet()
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    return [
        Spacer(1, 0.3 * inch),
        Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Trading System Analytics", small),
    ]


def export_trade_pdf(report: TradeReportData) -> bytes:
    buf = io.BytesIO()
    doc = _make_doc(buf)
    styles = getSampleStyleSheet()
    elements = _header("Trade Report", f"ID: {report.trade_id}")

    pnl_str = f"${report.net_pnl:+,.6f}" if report.net_pnl is not None else "Open"
    gross_str = f"${report.gross_pnl:+,.6f}" if report.gross_pnl is not None else "Open"

    rows = [
        ["Field", "Value"],
        ["Date & Time", report.datetime],
        ["Asset / Pair", report.asset],
        ["Strategy", report.strategy],
        ["Trade Type", report.trade_type],
        ["Entry Price", f"${report.entry_price:,.6f}"],
        ["Exit Price", f"${report.exit_price:,.6f}" if report.exit_price else "Open"],
        ["Stop Loss", f"${report.stop_loss:,.6f}" if report.stop_loss else "—"],
        ["Take Profit", f"${report.take_profit:,.6f}" if report.take_profit else "—"],
        ["Quantity", str(report.quantity)],
        ["Fees Paid", f"${report.fees_paid:,.6f}"],
        ["Slippage", f"${report.slippage:,.6f}"],
        ["Gross P&L", gross_str],
        ["Net P&L", pnl_str],
        ["P&L %", f"{report.pnl_percent:+.2f}%" if report.pnl_percent is not None else "—"],
        ["Risk : Reward", f"1 : {report.risk_reward_ratio}" if report.risk_reward_ratio else "—"],
        ["Duration", report.trade_duration],
        ["Signal Reason", report.signal_reason or "—"],
        ["Exit Reason", report.exit_reason or "—"],
        ["Market Condition", report.market_condition or "—"],
        ["Mode", report.mode.upper()],
        ["Broker", report.broker or "—"],
        ["Notes", report.notes or "—"],
        ["Emotions", report.emotions or "—"],
        ["Mistakes", report.mistakes or "—"],
    ]

    table = Table(rows, colWidths=[2.2 * inch, 4.8 * inch])
    table.setStyle(_BASE_TABLE_STYLE)

    # Highlight Net P&L row
    if report.net_pnl is not None:
        fill = _GREEN if report.net_pnl > 0 else _RED
        net_row = next(i for i, r in enumerate(rows) if r[0] == "Net P&L")
        table.setStyle(TableStyle([("BACKGROUND", (0, net_row), (-1, net_row), fill)]))

    elements.append(table)

    if report.screenshot_url:
        elements += [
            Spacer(1, 0.2 * inch),
            Paragraph(f"Chart: {report.screenshot_url}", styles["Normal"]),
        ]

    elements += _footer_text()
    doc.build(elements)
    buf.seek(0)
    return buf.read()


def export_daily_pdf(summary: Dict) -> bytes:
    buf = io.BytesIO()
    doc = _make_doc(buf)
    elements = _header(f"Daily Report", f"Date: {summary.get('date', '')}")

    pnl = summary.get("net_pnl", 0)
    pnl_color = _GREEN if pnl >= 0 else _RED

    metrics = [
        ["Metric", "Value"],
        ["Total Trades", str(summary.get("total_trades", 0))],
        ["Wins / Losses", f"{summary.get('winning_trades', 0)} / {summary.get('losing_trades', 0)}"],
        ["Win Rate", f"{summary.get('win_rate', 0):.1f}%"],
        ["Net P&L", f"${pnl:+,.4f}"],
        ["Gross Profit", f"${summary.get('gross_profit', 0):,.4f}"],
        ["Gross Loss", f"${summary.get('gross_loss', 0):,.4f}"],
        ["Fees Paid", f"${summary.get('fees_paid', 0):,.4f}"],
        ["Max Drawdown", f"${summary.get('max_drawdown', 0):,.4f}"],
        ["Avg Win", f"${summary.get('avg_win', 0):,.4f}"],
        ["Avg Loss", f"${summary.get('avg_loss', 0):,.4f}"],
        ["Avg R : R", f"1 : {summary.get('avg_rr', 0):.2f}"],
        ["Profit Factor", f"{summary.get('profit_factor', 0):.2f}"],
        ["Mistakes Found", str(summary.get("mistakes_count", 0))],
    ]

    table = Table(metrics, colWidths=[3 * inch, 3 * inch])
    table.setStyle(_BASE_TABLE_STYLE)

    pnl_row = next(i for i, r in enumerate(metrics) if r[0] == "Net P&L")
    table.setStyle(TableStyle([("BACKGROUND", (0, pnl_row), (-1, pnl_row), pnl_color)]))

    elements.append(table)

    recs = summary.get("recommendations", [])
    if recs:
        styles = getSampleStyleSheet()
        elements += [
            Spacer(1, 0.25 * inch),
            Paragraph("Recommendations", styles["Heading2"]),
        ]
        for i, rec in enumerate(recs, 1):
            elements.append(Paragraph(f"{i}. {rec}", styles["Normal"]))

    elements += _footer_text()
    doc.build(elements)
    buf.seek(0)
    return buf.read()


def export_monthly_pdf(summary: Dict) -> bytes:
    buf = io.BytesIO()
    doc = _make_doc(buf)
    import calendar
    month_name = calendar.month_name[summary.get("month", 1)]
    elements = _header("Monthly Report", f"{month_name} {summary.get('year', '')}")

    metrics = [
        ["Metric", "Value"],
        ["Total Trades", str(summary.get("total_trades", 0))],
        ["Win Rate", f"{summary.get('win_rate', 0):.1f}%"],
        ["Net P&L", f"${summary.get('net_pnl', 0):+,.4f}"],
        ["Max Drawdown", f"${summary.get('max_drawdown', 0):,.4f}"],
        ["Avg R : R", f"1 : {summary.get('avg_rr', 0):.2f}"],
        ["Profit Factor", f"{summary.get('profit_factor', 0):.2f}"],
        ["Sharpe Ratio", f"{summary.get('sharpe_ratio', 0):.4f}" if summary.get("sharpe_ratio") else "—"],
    ]

    table = Table(metrics, colWidths=[3 * inch, 3 * inch])
    table.setStyle(_BASE_TABLE_STYLE)

    pnl = summary.get("net_pnl", 0)
    pnl_row = next(i for i, r in enumerate(metrics) if r[0] == "Net P&L")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, pnl_row), (-1, pnl_row), _GREEN if pnl >= 0 else _RED)
    ]))
    elements.append(table)

    # Strategy breakdown table
    strategy_bd = summary.get("strategy_breakdown", {})
    if strategy_bd:
        styles = getSampleStyleSheet()
        elements += [Spacer(1, 0.25 * inch), Paragraph("Strategy Breakdown", styles["Heading2"])]
        s_rows = [["Strategy", "Trades", "Win Rate", "Net P&L", "Avg R:R"]]
        for strat, data in strategy_bd.items():
            s_rows.append([
                strat,
                str(data.get("trades", 0)),
                f"{data.get('win_rate', 0):.1f}%",
                f"${data.get('net_pnl', 0):+,.4f}",
                f"1:{data.get('avg_rr', 0):.2f}",
            ])
        st = Table(s_rows, colWidths=[2 * inch, 1 * inch, 1 * inch, 1.5 * inch, 1 * inch])
        st.setStyle(_BASE_TABLE_STYLE)
        elements.append(st)

    recs = summary.get("improvement_suggestions", [])
    if recs:
        styles = getSampleStyleSheet()
        elements += [Spacer(1, 0.25 * inch), Paragraph("Improvement Suggestions", styles["Heading2"])]
        for i, rec in enumerate(recs, 1):
            elements.append(Paragraph(f"{i}. {rec}", styles["Normal"]))

    elements += _footer_text()
    doc.build(elements)
    buf.seek(0)
    return buf.read()
