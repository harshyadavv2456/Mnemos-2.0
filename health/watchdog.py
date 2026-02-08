"""
MNEMOS 2.1 - Watchdog: memory/CPU guardrails, crash detection, restart limits.
"""
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional

from config.settings import WATCHDOG_MAX_MEMORY_MB, WATCHDOG_MAX_RESTARTS_PER_HOUR
from storage.db import cursor, get_restart_count_since, insert_restart

logger = logging.getLogger(__name__)


def get_memory_mb() -> float:
    """Current process RSS in MB (best-effort cross-platform)."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0  # Linux: KB
    except Exception:
        pass
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        pass
    return 0.0


def check_memory_guardrail() -> bool:
    """True if within limit; False if over (caller may exit/restart)."""
    mb = get_memory_mb()
    if mb <= 0:
        return True
    if mb > WATCHDOG_MAX_MEMORY_MB:
        logger.warning("Watchdog: memory %.1f MB exceeds limit %.1f MB", mb, WATCHDOG_MAX_MEMORY_MB)
        return False
    return True


def check_restart_guardrail() -> bool:
    """True if restarts in last hour < limit; False if too many restarts."""
    since = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    with cursor() as cur:
        n = get_restart_count_since(cur, since)
    if n >= WATCHDOG_MAX_RESTARTS_PER_HOUR:
        logger.warning("Watchdog: %d restarts in last hour (max %d)", n, WATCHDOG_MAX_RESTARTS_PER_HOUR)
        return False
    return True


def record_restart(reason: str, restart_count: int) -> None:
    """Log restart to DB."""
    try:
        with cursor() as cur:
            insert_restart(cur, reason, restart_count)
    except Exception as e:
        logger.warning("Failed to record restart: %s", e)


def should_allow_restart() -> bool:
    """True if both memory and restart guardrails allow a restart."""
    return check_memory_guardrail() and check_restart_guardrail()
