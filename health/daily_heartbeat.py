"""
MNEMOS 2.1 - Daily heartbeat to Telegram: uptime summary, restart count, last status.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from config.settings import DAILY_HEARTBEAT_HOUR_UTC, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from storage.db import cursor

logger = logging.getLogger(__name__)

_LAST_DAILY_SENT: Optional[datetime] = None


def _send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        import urllib.request
        import urllib.parse
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        body = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text[:4096],
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        data = urllib.parse.urlencode(body).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:
        logger.warning("Daily heartbeat Telegram failed: %s", e)
        return False


def _get_heartbeat_summary() -> str:
    """Query last 24h heartbeats and restarts."""
    since = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
    lines: list[str] = []
    try:
        with cursor() as cur:
            cur.execute("SELECT status, COUNT(*) FROM heartbeats WHERE ts >= ? GROUP BY status", (since,))
            for row in cur.fetchall():
                lines.append(f"  {row[0]}: {row[1]}")
            cur.execute("SELECT COUNT(*) FROM restarts WHERE ts >= ?", (since,))
            r = cur.fetchone()
            restarts = r[0] if r else 0
            lines.append(f"  Restarts (24h): {restarts}")
            cur.execute("SELECT ts, status, message FROM heartbeats ORDER BY ts DESC LIMIT 1")
            last = cur.fetchone()
            if last:
                lines.append(f"  Last: {last[1]} - {last[2] or ''}")
    except Exception as e:
        lines.append(f"  Error: {e}")
    return "\n".join(lines) if lines else "No data"


def maybe_send_daily_heartbeat(force: bool = False) -> bool:
    """
    Send daily heartbeat to Telegram if we're in the configured hour (UTC) and haven't sent today.
    Returns True if sent.
    """
    global _LAST_DAILY_SENT
    now = datetime.utcnow()
    if not force and now.hour != DAILY_HEARTBEAT_HOUR_UTC:
        return False
    if _LAST_DAILY_SENT and (_LAST_DAILY_SENT.date() >= now.date()):
        return False
    summary = _get_heartbeat_summary()
    msg = (
        "<b>MNEMOS 2.1 – Daily Heartbeat</b>\n"
        f"Date: {now.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        "<b>Last 24h summary</b>\n"
        f"{summary}"
    )
    if _send_telegram(msg):
        _LAST_DAILY_SENT = now
        logger.info("Daily heartbeat sent to Telegram")
        return True
    return False
