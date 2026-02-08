"""
MNEMOS 2.1 - Alert dispatcher: Telegram + Email with de-dup and severity.
"""
import logging
from typing import Optional

from alerts.dedup import can_send_alert, record_alert_sent
from alerts.email_alert import send_friction_email
from alerts.telegram_alert import send_friction_alert

logger = logging.getLogger(__name__)


def dispatch_friction(
    symbol: str,
    score: float,
    explanation: str,
    headline: Optional[str] = None,
    signal_type: Optional[str] = None,
) -> None:
    """Send friction to Telegram and Email if de-dup allows. Optional GROQ analysis appended."""
    if signal_type is None:
        signal_type = "unknown"
    allowed, reason = can_send_alert(symbol, signal_type)
    if not allowed:
        logger.debug("Alert skipped (dedup): %s %s - %s", symbol, signal_type, reason)
        return
    groq_analysis = None
    try:
        from engine.groq_analysis import analyze_signal
        groq_analysis = analyze_signal(symbol, score, explanation)
    except Exception:
        pass
    sent_tg = send_friction_alert(symbol, score, explanation, headline, groq_analysis)
    sent_em = send_friction_email(symbol, score, explanation, groq_analysis)
    if sent_tg or sent_em:
        record_alert_sent(symbol, signal_type)
