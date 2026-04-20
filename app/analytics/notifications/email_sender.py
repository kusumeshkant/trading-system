from typing import Optional
from app.config.settings import get_settings
from app.core.logger import logger


async def send_email_report(
    subject: str,
    body_html: str,
    attachment: Optional[bytes] = None,
    attachment_name: str = "report.pdf",
) -> bool:
    settings = get_settings()
    if not getattr(settings, "email_host", None) or not getattr(settings, "email_user", None):
        logger.warning("email_not_configured")
        return False

    try:
        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = settings.email_user
        msg["To"] = settings.email_to
        msg.attach(MIMEText(body_html, "html"))

        if attachment:
            part = MIMEApplication(attachment, Name=attachment_name)
            part["Content-Disposition"] = f'attachment; filename="{attachment_name}"'
            msg.attach(part)

        await aiosmtplib.send(
            msg,
            hostname=settings.email_host,
            port=getattr(settings, "email_port", 587),
            username=settings.email_user,
            password=settings.email_password,
            use_tls=True,
        )
        return True
    except Exception as e:
        logger.error("email_send_failed", error=str(e))
        return False


def build_daily_email_html(summary: dict) -> str:
    pnl = summary.get("net_pnl", 0)
    pnl_color = "#22C55E" if pnl >= 0 else "#EF4444"
    rows_html = "\n".join(
        f'<tr style="background:{"#F0F4FF" if i % 2 == 0 else "white"};">'
        f'<td style="padding:8px 12px;font-weight:bold;">{label}</td>'
        f'<td style="padding:8px 12px;text-align:right;">{value}</td></tr>'
        for i, (label, value) in enumerate([
            ("Total Trades", summary.get("total_trades", 0)),
            ("Wins / Losses", f"{summary.get('winning_trades', 0)} / {summary.get('losing_trades', 0)}"),
            ("Win Rate", f"{summary.get('win_rate', 0):.1f}%"),
            ("Net P&L", f'<span style="color:{pnl_color};font-weight:bold;">${pnl:+,.4f}</span>'),
            ("Max Drawdown", f"${summary.get('max_drawdown', 0):,.4f}"),
            ("Avg R:R", f"1:{summary.get('avg_rr', 0):.2f}"),
            ("Profit Factor", f"{summary.get('profit_factor', 0):.2f}"),
            ("Mistakes Found", summary.get("mistakes_count", 0)),
        ])
    )

    recs = summary.get("recommendations", [])
    recs_html = "".join(f"<li style='margin-bottom:6px;'>{r}</li>" for r in recs)

    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;font-family:Arial,sans-serif;background:#F5F5F5;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:10px;
              box-shadow:0 2px 12px rgba(0,0,0,0.1);overflow:hidden;">
    <div style="background:#1A1A2E;padding:24px 30px;">
      <h1 style="color:#FFFFFF;margin:0;font-size:22px;">Daily Trading Report</h1>
      <p style="color:#4A9EFF;margin:6px 0 0;font-size:14px;">{summary.get('date', '')}</p>
    </div>
    <div style="padding:24px 30px;">
      <table style="width:100%;border-collapse:collapse;border:1px solid #CCCCCC;">
        <tr style="background:#1A1A2E;">
          <th style="padding:10px 12px;color:#fff;text-align:left;font-size:11px;">Metric</th>
          <th style="padding:10px 12px;color:#fff;text-align:right;font-size:11px;">Value</th>
        </tr>
        {rows_html}
      </table>
      <div style="margin-top:20px;background:#FFFDE7;border-left:4px solid #F59E0B;
                  padding:16px;border-radius:4px;">
        <h3 style="margin:0 0 10px;color:#1A1A2E;font-size:14px;">Recommendations</h3>
        <ul style="margin:0;padding-left:20px;font-size:13px;">{recs_html}</ul>
      </div>
    </div>
    <div style="background:#F9F9F9;padding:12px 30px;text-align:center;">
      <p style="color:#999;font-size:11px;margin:0;">Trading System Analytics — Auto-generated report</p>
    </div>
  </div>
</body>
</html>"""
