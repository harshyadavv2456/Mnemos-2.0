"""
MNEMOS 2.1 - Supervisor: automatic restart loop with delay and guardrails.
"""
import logging
import sys
import time
from pathlib import Path
from typing import Callable, Optional

from config.settings import SUPERVISOR_RESTART_DELAY_SEC
from health.watchdog import record_restart, should_allow_restart

logger = logging.getLogger(__name__)


def run_supervised(
    main_fn: Callable[[], None],
    max_restarts: Optional[int] = None,
) -> None:
    """
    Run main_fn in a loop. On exception: log, record restart, wait, then restart.
    Stops if guardrails forbid restart or max_restarts exceeded.
    """
    restart_count = 0
    while True:
        try:
            main_fn()
            # main_fn returned normally (e.g. --once)
            break
        except KeyboardInterrupt:
            logger.info("Supervisor: interrupted")
            break
        except Exception as e:
            restart_count += 1
            logger.exception("Supervisor: run failed (restart %d): %s", restart_count, e)
            record_restart(str(e)[:200], restart_count)
            if max_restarts is not None and restart_count >= max_restarts:
                logger.error("Supervisor: max restarts %d reached; exiting", max_restarts)
                sys.exit(1)
            if not should_allow_restart():
                logger.error("Supervisor: guardrails forbid restart; exiting")
                sys.exit(1)
            logger.info("Supervisor: waiting %s s before restart", SUPERVISOR_RESTART_DELAY_SEC)
            time.sleep(SUPERVISOR_RESTART_DELAY_SEC)
