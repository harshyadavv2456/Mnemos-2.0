"""
MNEMOS 2.1 - Main orchestrator: fetch -> risk filter -> features -> friction -> confidence -> store -> alert (with dedup).
Outcome backfill, daily heartbeat, weekly/monthly reports.
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd

from config.settings import (
    CONFIDENCE_ALERT_THRESHOLD,
    FRICTION_ALERT_THRESHOLD,
    get_watchlist,
)
from core.data_fetcher import fetch_daily_for_features, fetch_latest_bars
from core.feature_engineering import build_features_for_symbols
from engine.friction_engine import FrictionResult, compute_friction_batch
from engine.uptime import log_heartbeat
from engine.confidence_engine import compute_confidence, should_alert_by_confidence
from alerts.dispatcher import dispatch_friction
from alerts.dedup import infer_signal_type, severity_from_score
from storage.db import cursor, init_db, insert_prices, insert_signal
from storage.backup import run_backups
from risk.governance import apply_risk_filters
from analytics.attribution import update_outcomes_for_signal
from health.daily_heartbeat import maybe_send_daily_heartbeat
from reports.generator import run_weekly_report_and_deliver, run_monthly_report_and_deliver
from config.settings import WEEKLY_REPORT_DAY, MONTHLY_REPORT_DAY

logger = logging.getLogger(__name__)

# Optional: set from Colab after mounting Drive
DRIVE_MOUNT_PATH: Optional[Path] = None


def set_drive_mount(path: Optional[Path]) -> None:
    global DRIVE_MOUNT_PATH
    DRIVE_MOUNT_PATH = path


def _outcome_backfill() -> None:
    """Update outcomes for signals that have no outcome yet; use latest price at or before signal time."""
    since = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"
    with cursor() as cur:
        cur.execute(
            """SELECT s.id, s.symbol, s.created_at
             FROM signals s
             LEFT JOIN outcomes o ON o.signal_id = s.id
             WHERE s.created_at >= ? AND o.id IS NULL""",
            (since,),
        )
        rows = cur.fetchall()
    for r in rows:
        signal_id, symbol, created_at = r[0], r[1], r[2]
        with cursor() as c2:
            c2.execute(
                "SELECT close FROM prices WHERE symbol = ? AND dt <= ? ORDER BY dt DESC LIMIT 1",
                (symbol, created_at),
            )
            row2 = c2.fetchone()
        price_at_signal = float(row2[0]) if row2 and row2[0] is not None else None
        if price_at_signal and price_at_signal > 0:
            try:
                update_outcomes_for_signal(signal_id, symbol, created_at, price_at_signal)
            except Exception as e:
                logger.debug("Outcome backfill %s: %s", signal_id, e)


def _tick() -> None:
    """Single cycle: fetch -> risk filter -> features -> friction -> confidence -> store -> alert."""
    symbols = get_watchlist()
    if not symbols:
        logger.warning("Watchlist empty; skip tick")
        return

    log_heartbeat("tick_start", f"symbols={len(symbols)}")

    # 1) Latest bars (for storage)
    try:
        df_latest = fetch_latest_bars(symbols, interval_min=5)
        if df_latest is not None and not df_latest.empty:
            with cursor() as cur:
                insert_prices(cur, df_latest)
    except Exception as e:
        logger.warning("Fetch latest failed: %s", e)

    # 2) Daily for features
    try:
        df_daily = fetch_daily_for_features(symbols, days=30)
    except Exception as e:
        logger.warning("Fetch daily failed: %s", e)
        df_daily = pd.DataFrame()

    if df_daily is None or df_daily.empty:
        log_heartbeat("no_data", "daily fetch empty")
        return

    # 3) Features
    features_by_symbol = build_features_for_symbols(df_daily, symbols, lookback_days=20)
    if not features_by_symbol:
        log_heartbeat("no_features", "build_features empty")
        return

    # 4) Risk filter
    symbols_passed = apply_risk_filters(symbols, features_by_symbol)
    features_by_symbol = {k: v for k, v in features_by_symbol.items() if k in symbols_passed}

    # 5) Friction
    results: List[FrictionResult] = compute_friction_batch(features_by_symbol, fetch_news=True)

    # 6) Confidence, store, alert
    now_dt = datetime.utcnow().isoformat() + "Z"
    for r in results:
        confidence = compute_confidence(r.symbol, r.score, features_by_symbol.get(r.symbol, {}), now_dt)
        severity = severity_from_score(r.score)
        signal_type = getattr(r, "signal_type", None) or infer_signal_type(r.signals)
        try:
            with cursor() as cur:
                signal_id = insert_signal(
                    cur,
                    r.symbol,
                    r.score,
                    r.explanation,
                    json.dumps(r.signals),
                    signal_type=signal_type,
                    confidence=confidence,
                    severity=severity,
                )
            # Outcome backfill: we need price_at_signal. Use latest close from daily for this symbol.
            sub = df_daily[df_daily["symbol"] == r.symbol] if not df_daily.empty else pd.DataFrame()
            if not sub.empty and "Close" in sub.columns:
                price_at_signal = float(sub["Close"].iloc[-1])
                if price_at_signal > 0:
                    update_outcomes_for_signal(signal_id, r.symbol, now_dt, price_at_signal)
        except Exception as e:
            logger.warning("Insert signal failed %s: %s", r.symbol, e)
            continue

        # Alert only if both friction and confidence above threshold, and dedup allows
        if r.score >= FRICTION_ALERT_THRESHOLD and should_alert_by_confidence(confidence):
            headline = r.signals[0] if r.signals else None
            dispatch_friction(r.symbol, r.score, r.explanation, headline, signal_type)

    log_heartbeat("ok", f"friction_computed={len(results)}")


def run_backup_cycle() -> None:
    """Run local + optional Drive backup."""
    try:
        run_backups(DRIVE_MOUNT_PATH)
        log_heartbeat("backup", "ok")
    except Exception as e:
        logger.warning("Backup failed: %s", e)
        log_heartbeat("backup_fail", str(e)[:100])


def run_daily_tasks(tick_count: int) -> None:
    """Daily heartbeat, outcome backfill, weekly/monthly reports."""
    maybe_send_daily_heartbeat()
    try:
        _outcome_backfill()
    except Exception as e:
        logger.warning("Outcome backfill failed: %s", e)
    now = datetime.utcnow()
    if now.weekday() == WEEKLY_REPORT_DAY and now.hour == 4:
        try:
            run_weekly_report_and_deliver()
        except Exception as e:
            logger.warning("Weekly report failed: %s", e)
    if now.day == MONTHLY_REPORT_DAY and now.hour == 4:
        try:
            run_monthly_report_and_deliver()
        except Exception as e:
            logger.warning("Monthly report failed: %s", e)


def run_once() -> None:
    """Single run (for testing or cron-style)."""
    init_db()
    _tick()


def run_forever(backup_interval_ticks: int = 20, daily_task_interval_ticks: int = 60) -> None:
    """Run adaptive loop forever. Backup and daily tasks on intervals."""
    init_db()
    from engine.scheduler import run_adaptive_loop

    tick_count = [0]

    def on_tick() -> None:
        tick_count[0] += 1
        _tick()
        if tick_count[0] % backup_interval_ticks == 0:
            run_backup_cycle()
        if tick_count[0] % daily_task_interval_ticks == 0:
            run_daily_tasks(tick_count[0])

    def on_error(exc: Exception) -> None:
        log_heartbeat("error", str(exc)[:200])

    run_adaptive_loop(on_tick, on_error=on_error)
