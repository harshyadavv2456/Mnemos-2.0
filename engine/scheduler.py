"""
MNEMOS 2.0 - Adaptive polling: market hours 2-3 min, off hours 30 min.
Auto-resume on failure.
"""
import logging
import time
from datetime import datetime
from typing import Callable, Optional

import pytz

from config.settings import (
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MIN,
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MIN,
    POLL_INTERVAL_MARKET_MIN,
    POLL_INTERVAL_OFF_MIN,
)

logger = logging.getLogger(__name__)
IST = pytz.timezone("Asia/Kolkata")


def is_market_hours(utc_now: Optional[datetime] = None) -> bool:
    """True if NSE market is open (IST 9:15 - 15:30)."""
    if utc_now is None:
        utc_now = datetime.utcnow()
    now_ist = pytz.utc.localize(utc_now).astimezone(IST)
    open_minutes = MARKET_OPEN_HOUR * 60 + MARKET_OPEN_MIN
    close_minutes = MARKET_CLOSE_HOUR * 60 + MARKET_CLOSE_MIN
    current_minutes = now_ist.hour * 60 + now_ist.minute
    if now_ist.weekday() >= 5:  # Sat, Sun
        return False
    return open_minutes <= current_minutes < close_minutes


def get_poll_interval_seconds() -> int:
    """Current poll interval in seconds (market vs off hours)."""
    if is_market_hours():
        return POLL_INTERVAL_MARKET_MIN * 60
    return POLL_INTERVAL_OFF_MIN * 60


def run_adaptive_loop(
    tick_callback: Callable[[], None],
    on_error: Optional[Callable[[Exception], None]] = None,
    max_iterations: Optional[int] = None,
) -> None:
    """
    Run tick_callback every adaptive interval. On exception call on_error and continue.
    If max_iterations set, stop after that many ticks (for testing).
    """
    count = 0
    while True:
        try:
            tick_callback()
            count += 1
            if max_iterations is not None and count >= max_iterations:
                break
        except Exception as e:
            logger.exception("Scheduler tick failed: %s", e)
            if on_error:
                try:
                    on_error(e)
                except Exception:
                    pass
        interval = get_poll_interval_seconds()
        logger.debug("Next tick in %s s (market=%s)", interval, is_market_hours())
        time.sleep(interval)
