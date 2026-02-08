"""
MNEMOS 2.1 - Performance attribution: track outcomes at +1D, +3D, +5D.
Compute win rate, avg return, drawdown, latency. Store in SQLite.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd

from storage.db import cursor, insert_outcome

logger = logging.getLogger(__name__)


def get_latest_close_by_symbol(cur, symbol: str) -> Optional[Tuple[str, float]]:
    """(dt, close) for latest price row for symbol."""
    cur.execute(
        "SELECT dt, close FROM prices WHERE symbol = ? AND close IS NOT NULL ORDER BY dt DESC LIMIT 1",
        (symbol[:32],),
    )
    row = cur.fetchone()
    if row:
        return (row[0], float(row[1]))
    return None


def get_close_on_date(cur, symbol: str, dt_str: str) -> Optional[float]:
    """Closest close on or after dt_str for symbol (for +1D, +3D, +5D). dt_str can be date or datetime."""
    cur.execute(
        "SELECT close FROM prices WHERE symbol = ? AND dt >= ? AND close IS NOT NULL ORDER BY dt ASC LIMIT 1",
        (symbol[:32], dt_str[:10]),
    )
    row = cur.fetchone()
    return float(row[0]) if row else None


def compute_returns(
    price_at_signal: float,
    close_1d: Optional[float],
    close_3d: Optional[float],
    close_5d: Optional[float],
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Return (return_1d_pct, return_3d_pct, return_5d_pct)."""
    if price_at_signal <= 0:
        return None, None, None
    r1 = (close_1d - price_at_signal) / price_at_signal * 100.0 if close_1d is not None else None
    r3 = (close_3d - price_at_signal) / price_at_signal * 100.0 if close_3d is not None else None
    r5 = (close_5d - price_at_signal) / price_at_signal * 100.0 if close_5d is not None else None
    return r1, r3, r5


def update_outcomes_for_signal(signal_id: int, symbol: str, signal_dt: str, price_at_signal: float) -> None:
    """
    Compute +1D, +3D, +5D returns from prices table and insert into outcomes.
    signal_dt: ISO date/datetime of signal. We use next trading days for 1d/3d/5d.
    """
    with cursor() as cur:
        # Check if outcome already exists for this signal
        cur.execute("SELECT id FROM outcomes WHERE signal_id = ?", (signal_id,))
        if cur.fetchone():
            return
        try:
            base_dt = datetime.fromisoformat(signal_dt.replace("Z", "").split("+")[0].strip())
        except Exception:
            base_dt = datetime.utcnow()
        # Simple: next 1, 3, 5 calendar days (then find closest trading data)
        d1 = (base_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        d3 = (base_dt + timedelta(days=3)).strftime("%Y-%m-%d")
        d5 = (base_dt + timedelta(days=5)).strftime("%Y-%m-%d")
        close_1d = get_close_on_date(cur, symbol, d1)
        close_3d = get_close_on_date(cur, symbol, d3)
        close_5d = get_close_on_date(cur, symbol, d5)
        r1, r3, r5 = compute_returns(price_at_signal, close_1d, close_3d, close_5d)
        insert_outcome(
            cur,
            signal_id=signal_id,
            symbol=symbol,
            signal_dt=signal_dt,
            price_at_signal=price_at_signal,
            return_1d=r1,
            return_3d=r3,
            return_5d=r5,
            outcome_1d_dt=d1 if close_1d else None,
            outcome_3d_dt=d3 if close_3d else None,
            outcome_5d_dt=d5 if close_5d else None,
        )


def get_attribution_stats(symbol: Optional[str] = None, min_samples: int = 5) -> Dict:
    """
    Aggregate win rate, avg return, drawdown, latency from outcomes.
    symbol: optional filter. Returns dict with win_rate_1d, win_rate_3d, win_rate_5d,
    avg_return_1d, avg_return_3d, avg_return_5d, max_drawdown_1d, sample_count.
    """
    with cursor() as cur:
        if symbol:
            cur.execute(
                """SELECT return_1d, return_3d, return_5d FROM outcomes
                   WHERE symbol = ? AND (return_1d IS NOT NULL OR return_3d IS NOT NULL OR return_5d IS NOT NULL)""",
                (symbol[:32],),
            )
        else:
            cur.execute(
                """SELECT return_1d, return_3d, return_5d FROM outcomes
                   WHERE return_1d IS NOT NULL OR return_3d IS NOT NULL OR return_5d IS NOT NULL"""
            )
        rows = cur.fetchall()
    if not rows or len(rows) < min_samples:
        return {
            "win_rate_1d": None,
            "win_rate_3d": None,
            "win_rate_5d": None,
            "avg_return_1d": None,
            "avg_return_3d": None,
            "avg_return_5d": None,
            "max_drawdown_1d": None,
            "sample_count": len(rows),
        }
    r1 = [float(r[0]) for r in rows if r[0] is not None]
    r3 = [float(r[1]) for r in rows if r[1] is not None]
    r5 = [float(r[2]) for r in rows if r[2] is not None]

    def win_rate(vals: List[float]) -> Optional[float]:
        if not vals:
            return None
        return sum(1 for x in vals if x > 0) / len(vals) * 100.0

    def avg(vals: List[float]) -> Optional[float]:
        if not vals:
            return None
        return sum(vals) / len(vals)

    def max_dd(vals: List[float]) -> Optional[float]:
        if not vals:
            return None
        peak = vals[0]
        md = 0.0
        for x in vals:
            if x > peak:
                peak = x
            dd = peak - x
            if dd > md:
                md = dd
        return md

    return {
        "win_rate_1d": round(win_rate(r1), 2) if r1 else None,
        "win_rate_3d": round(win_rate(r3), 2) if r3 else None,
        "win_rate_5d": round(win_rate(r5), 2) if r5 else None,
        "avg_return_1d": round(avg(r1), 2) if r1 else None,
        "avg_return_3d": round(avg(r3), 2) if r3 else None,
        "avg_return_5d": round(avg(r5), 2) if r5 else None,
        "max_drawdown_1d": round(max_dd(r1), 2) if r1 else None,
        "sample_count": len(rows),
    }
