import io
import csv
from dataclasses import asdict
from typing import List, Dict
from app.analytics.reports.trade_report import TradeReportData


def export_trades_csv(reports: List[TradeReportData]) -> bytes:
    if not reports:
        return b""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(asdict(reports[0]).keys()))
    writer.writeheader()
    for r in reports:
        writer.writerow(asdict(r))
    return output.getvalue().encode("utf-8")


def export_daily_summaries_csv(summaries: List[Dict]) -> bytes:
    if not summaries:
        return b""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(summaries[0].keys()))
    writer.writeheader()
    writer.writerows(summaries)
    return output.getvalue().encode("utf-8")
