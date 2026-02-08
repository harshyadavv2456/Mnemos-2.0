"""
MNEMOS 2.1 - Signal de-duplication: cooldown windows, symbol + signal-type locking, severity escalation.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from config.settings import ALERT_COOLDOWN_SYMBOL_MINUTES, SIGNAL_COOLDOWN_MINUTES
from storage.db import cursor, get_alert_lock, upsert_alert_lock

logger = logging.getLogger(__name__)

# Signal type constants (must match friction_engine first-signal prefixes)
SIGNAL_TYPE_PANIC = "panic_selling"
SIGNAL_TYPE_ACCUMULATION = "silent_accumulation"
SIGNAL_TYPE_SECTOR_LAG = "sector_lag"
SIGNAL_TYPE_NEWS = "news_underreaction"
SIGNAL_TYPE_OVERREACTION = "overreaction"
SIGNAL_TYPE_UNKNOWN = "unknown"


def infer_signal_type(signals: list) -> str:
    """Infer signal_type from first signal string."""
    if not signals:
        return SIGNAL_TYPE_UNKNOWN
    first = (signals[0] or "").lower()
    if "panic" in first:
        return SIGNAL_TYPE_PANIC
    if "accumulation" in first or "silent" in first:
        return SIGNAL_TYPE_ACCUMULATION
    if "sector" in first or "lag" in first:
        return SIGNAL_TYPE_SECTOR_LAG
    if "news" in first or "headline" in first:
        return SIGNAL_TYPE_NEWS
    if "overreaction" in first:
        return SIGNAL_TYPE_OVERREACTION
    return SIGNAL_TYPE_UNKNOWN


def severity_from_score(score: float) -> int:
    """1=low, 2=medium, 3=high, 4=critical."""
    if score >= 0.85:
        return 4
    if score >= 0.75:
        return 3
    if score >= 0.65:
        return 2
    return 1


def can_send_alert(symbol: str, signal_type: str) -> Tuple[bool, Optional[str]]:
    """
    True if alert is allowed (past cooldown for this symbol+signal_type).
    Returns (allowed, reason_if_not).
    """
    with cursor() as cur:
        last_ts = get_alert_lock(cur, symbol, signal_type)
    if not last_ts:
        return True, None
    try:
        # last_ts is ISO UTC (e.g. ...Z)
        last_naive = datetime.fromisoformat(last_ts.replace("Z", "").split("+")[0].strip())
        now_naive = datetime.utcnow()
        delta_min = (now_naive - last_naive).total_seconds() / 60.0
        if delta_min < ALERT_COOLDOWN_SYMBOL_MINUTES:
            return False, f"Cooldown: {ALERT_COOLDOWN_SYMBOL_MINUTES - int(delta_min)} min left"
    except Exception as e:
        logger.debug("Parse last_alert_ts: %s", e)
        return True, None
    return True, None


def record_alert_sent(symbol: str, signal_type: str) -> None:
    """Record that an alert was sent (for cooldown)."""
    try:
        with cursor() as cur:
            upsert_alert_lock(cur, symbol, signal_type)
    except Exception as e:
        logger.warning("Failed to record alert lock: %s", e)
