"""
MNEMOS 2.0 - Heartbeat logger, crash detection, auto-restart, Colab keepalive.
"""
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from storage.db import cursor, insert_heartbeat

logger = logging.getLogger(__name__)

_LAST_HEARTBEAT: float = 0
HEARTBEAT_INTERVAL_SEC = 120


def log_heartbeat(status: str = "ok", message: Optional[str] = None) -> None:
    """Write heartbeat to DB and optionally stdout (for Colab visibility)."""
    global _LAST_HEARTBEAT
    now = time.time()
    if now - _LAST_HEARTBEAT < HEARTBEAT_INTERVAL_SEC and status == "ok":
        return
    _LAST_HEARTBEAT = now
    try:
        with cursor() as cur:
            insert_heartbeat(cur, status, message)
    except Exception as e:
        logger.warning("Heartbeat write failed: %s", e)
    ts = datetime.utcnow().isoformat() + "Z"
    line = f"[MNEMOS] {ts} heartbeat {status}" + (f" {message}" if message else "")
    logger.info(line)
    print(line, flush=True)


def colab_keepalive_js() -> str:
    """
    Return JavaScript snippet to run in Colab to click 'Connect' and prevent disconnect.
    User can run this in browser console or via Colab notebook cell with %%javascript.
    """
    return """
    // Colab keepalive: reconnect / prevent idle disconnect (run in notebook or console)
    function clickConnect(){
      console.log("MNEMOS keepalive: checking connection");
      const b = document.querySelector(".colab-connect-button");
      if (b) b.click();
    }
    setInterval(clickConnect, 60000);
    """


def colab_keepalive_cell_instructions() -> str:
    """Instructions for user to add keepalive in Colab."""
    return (
        "To reduce disconnects: Runtime -> Run all, then keep tab active. "
        "For longer runs: add a new cell with: %%javascript\n"
        "  document.querySelector('.colab-connect-button')?.click();\n"
        "and run it every ~60 min, or use a browser extension to auto-refresh."
    )


def detect_crash_and_restart(
    main_script: Optional[str] = None,
    max_restarts: int = 5,
) -> None:
    """
    Optional: wrap main() so that on uncaught exception we restart (e.g. in Colab).
    main_script: path to script to re-exec (e.g. __file__). If None, just re-raise.
    """
    # In Colab we typically run from notebook; restart is "re-run all cells".
    # So this is a no-op unless running as standalone script with exec.
    if not main_script or not Path(main_script).exists():
        return
