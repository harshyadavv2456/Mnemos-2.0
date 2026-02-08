"""
MNEMOS 2.1 - Weekly intelligence report, monthly performance report. Markdown output; optional PDF.
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from analytics.attribution import get_attribution_stats
from config.settings import REPORTS_DIR
from storage.db import cursor

logger = logging.getLogger(__name__)


def _get_signal_counts_since(since_dt: str) -> List[tuple]:
    with cursor() as cur:
        cur.execute(
            "SELECT symbol, COUNT(*) FROM signals WHERE created_at >= ? GROUP BY symbol ORDER BY COUNT(*) DESC LIMIT 20",
            (since_dt,),
        )
        return cur.fetchall()


def _get_heartbeat_summary_since(since_dt: str) -> Dict[str, int]:
    with cursor() as cur:
        cur.execute(
            "SELECT status, COUNT(*) FROM heartbeats WHERE ts >= ? GROUP BY status",
            (since_dt,),
        )
        return dict(cur.fetchall())


def generate_weekly_report() -> str:
    """Markdown weekly intelligence report."""
    since = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
    signal_counts = _get_signal_counts_since(since)
    heartbeat = _get_heartbeat_summary_since(since)
    lines = [
        "# MNEMOS 2.1 – Weekly Intelligence Report",
        f"Period: last 7 days (to {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')})",
        "",
        "## Signal activity (top 20 symbols)",
        "",
    ]
    for sym, cnt in signal_counts:
        lines.append(f"- {sym}: {cnt} signals")
    lines.extend(["", "## System health (heartbeats)", ""])
    for status, cnt in heartbeat.items():
        lines.append(f"- {status}: {cnt}")
    lines.append("")
    return "\n".join(lines)


def generate_monthly_report() -> str:
    """Markdown monthly performance report (attribution + activity)."""
    since = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
    stats = get_attribution_stats(min_samples=1)
    signal_counts = _get_signal_counts_since(since)
    lines = [
        "# MNEMOS 2.1 – Monthly Performance Report",
        f"Period: last 30 days (to {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')})",
        "",
        "## Performance attribution",
        "",
        f"- Win rate (1D): {stats.get('win_rate_1d')}%",
        f"- Win rate (3D): {stats.get('win_rate_3d')}%",
        f"- Win rate (5D): {stats.get('win_rate_5d')}%",
        f"- Avg return 1D: {stats.get('avg_return_1d')}%",
        f"- Avg return 3D: {stats.get('avg_return_3d')}%",
        f"- Avg return 5D: {stats.get('avg_return_5d')}%",
        f"- Max drawdown 1D: {stats.get('max_drawdown_1d')}%",
        f"- Sample count: {stats.get('sample_count')}",
        "",
        "## Signal activity (top 20 symbols)",
        "",
    ]
    for sym, cnt in signal_counts:
        lines.append(f"- {sym}: {cnt} signals")
    lines.append("")
    return "\n".join(lines)


def save_report(content: str, kind: str) -> Path:
    """Save report to REPORTS_DIR. Returns path."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"{kind}_{ts}.md"
    path.write_text(content, encoding="utf-8")
    return path


def send_report_telegram(content: str) -> bool:
    """Send report to Telegram (truncated if long)."""
    from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    text = content[:4000] + "\n..." if len(content) > 4000 else content
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        body = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": True}
        data = urllib.parse.urlencode(body).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200
    except Exception as e:
        logger.warning("Report Telegram failed: %s", e)
        return False


def send_report_email(subject: str, body: str) -> bool:
    """Send report via email."""
    from alerts.email_alert import send_email
    return send_email(subject, body)


def run_weekly_report_and_deliver() -> Path:
    """Generate weekly report, save, send to Telegram + Email. Returns path."""
    content = generate_weekly_report()
    path = save_report(content, "weekly")
    send_report_telegram(content)
    send_report_email("MNEMOS 2.1 Weekly Intelligence Report", content)
    return path


def run_monthly_report_and_deliver() -> Path:
    """Generate monthly report, save, send to Telegram + Email. Returns path."""
    content = generate_monthly_report()
    path = save_report(content, "monthly")
    send_report_telegram(content)
    send_report_email("MNEMOS 2.1 Monthly Performance Report", content)
    return path
