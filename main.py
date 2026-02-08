#!/usr/bin/env python3
"""
MNEMOS 2.1 - Institutional-Grade Market Intelligence Platform.
Entrypoint: run with supervisor (auto-restart), or once/test.
Usage:
  python main.py              -> run forever with supervisor
  python main.py --once      -> single tick then exit
  python main.py --test      -> 2 symbols, one tick, exit
  python main.py --no-supervisor -> run forever without supervisor (for Colab)
"""
import argparse
import logging
import sys
from pathlib import Path

# Ensure project root on path (Colab and local)
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.settings import LOG_DIR, LOG_LEVEL

# ----- Logging -----
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / "mnemos.log"
level = getattr(logging, (LOG_LEVEL or "INFO").upper(), logging.INFO)
logging.basicConfig(
    level=level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def _validate_secrets() -> bool:
    """Optional: warn if Telegram/Email not set. Never log secret values."""
    from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GMAIL_USER, GMAIL_APP_PASSWORD
    ok = True
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID); alerts will skip Telegram.")
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        logger.warning("Gmail not configured; alerts will skip Email.")
    return ok


def _startup_checks() -> None:
    """Create dirs, init DB, validate config."""
    from config.settings import DATA_DIR, REPORTS_DIR
    from storage.db import init_db
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    _validate_secrets()


def main() -> None:
    parser = argparse.ArgumentParser(description="MNEMOS 2.1 - Market Intelligence")
    parser.add_argument("--once", action="store_true", help="Run single tick then exit")
    parser.add_argument("--test", action="store_true", help="Test run: 2 symbols, one tick, exit")
    parser.add_argument("--no-supervisor", action="store_true", help="Do not use supervisor (for Colab)")
    args = parser.parse_args()

    _startup_checks()

    if args.test:
        import os
        os.environ["MNEMOS_WATCHLIST"] = "RELIANCE.NS,TCS.NS"
        from engine.orchestrator import run_once
        run_once()
        logger.info("Test run complete")
        return

    if args.once:
        from engine.orchestrator import run_once
        run_once()
        return

    from engine.orchestrator import run_forever
    from health.supervisor import run_supervised

    logger.info("Starting MNEMOS 2.1 (adaptive loop)")

    def run_loop() -> None:
        run_forever(backup_interval_ticks=20, daily_task_interval_ticks=60)

    if args.no_supervisor:
        run_loop()
    else:
        run_supervised(run_loop, max_restarts=None)


if __name__ == "__main__":
    main()
