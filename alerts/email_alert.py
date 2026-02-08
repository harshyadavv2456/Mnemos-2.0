"""
MNEMOS 2.1 - Gmail SMTP email alerts. Multiple recipients (mail trail); rate limiting.
"""
import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from config.settings import (
    GMAIL_USER,
    GMAIL_APP_PASSWORD,
    ALERT_EMAIL_TO,
    EMAIL_MIN_INTERVAL_SEC,
)

logger = logging.getLogger(__name__)

_last_email_sent: float = 0


def _recipients_list(to: Optional[str] = None) -> List[str]:
    """Comma-separated ALERT_EMAIL_TO -> list of addresses (one mail trail)."""
    raw = to or ALERT_EMAIL_TO or ""
    if not raw:
        return []
    return [addr.strip() for addr in raw.split(",") if addr.strip()]


def _rate_limit() -> bool:
    global _last_email_sent
    now = time.time()
    if now - _last_email_sent < EMAIL_MIN_INTERVAL_SEC:
        return False
    _last_email_sent = now
    return True


def send_email(
    subject: str,
    body_text: str,
    to: Optional[str] = None,
) -> bool:
    """Send email via Gmail SMTP to all recipients (To: list = one thread; anyone can add others)."""
    recipients = _recipients_list(to)
    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not recipients:
        logger.debug("Email not configured; skip")
        return False
    if not _rate_limit():
        logger.debug("Email rate limit; skip")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject[:200]
        msg["From"] = GMAIL_USER
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, recipients, msg.as_string())
        logger.info("Email sent to %s", recipients)
        return True
    except Exception as e:
        logger.warning("Email send failed: %s", e)
        return False


def send_friction_email(
    symbol: str,
    score: float,
    explanation: str,
    groq_analysis: Optional[str] = None,
) -> bool:
    """Send friction alert email to all ALERT_EMAIL_TO recipients."""
    subject = f"MNEMOS 2.1 Friction: {symbol} (score {score:.2f})"
    body = f"Symbol: {symbol}\nScore: {score}\n\n{explanation}"
    if groq_analysis:
        body += f"\n\nAI analysis: {groq_analysis}"
    return send_email(subject, body)
