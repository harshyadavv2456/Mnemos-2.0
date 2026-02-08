"""
MNEMOS 2.1 - Backtesting framework: replay historical signals, evaluate rule effectiveness, rank patterns, CSV + report.
"""
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from storage.db import cursor
from config.settings import REPORTS_DIR

logger = logging.getLogger(__name__)


def load_signals_since(since_dt: str) -> List[Dict[str, Any]]:
    """Load signals from DB since given ISO datetime."""
    with cursor() as cur:
        cur.execute(
            """SELECT id, symbol, score, explanation, signals_json, created_at, signal_type, confidence
               FROM signals WHERE created_at >= ? ORDER BY created_at""",
            (since_dt,),
        )
        rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "symbol": r[1],
            "score": r[2],
            "explanation": r[3],
            "signals_json": r[4],
            "created_at": r[5],
            "signal_type": r[6] or "unknown",
            "confidence": r[7],
        }
        for r in rows
    ]


def load_outcomes_for_signals(signal_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Load outcomes keyed by signal_id."""
    if not signal_ids:
        return {}
    with cursor() as cur:
        placeholders = ",".join("?" * len(signal_ids))
        cur.execute(
            f"SELECT signal_id, return_1d, return_3d, return_5d FROM outcomes WHERE signal_id IN ({placeholders})",
            signal_ids,
        )
        rows = cur.fetchall()
    return {r[0]: {"return_1d": r[1], "return_3d": r[2], "return_5d": r[3]} for r in rows}


def run_backtest(since_dt: str) -> Dict[str, Any]:
    """
    Replay signals since since_dt, join outcomes, compute rule-level stats.
    Returns summary dict and list of signal-level rows for CSV.
    """
    signals = load_signals_since(since_dt)
    if not signals:
        return {"signals_count": 0, "by_type": {}, "rows": []}
    signal_ids = [s["id"] for s in signals]
    outcomes = load_outcomes_for_signals(signal_ids)
    rows: List[Dict[str, Any]] = []
    for s in signals:
        o = outcomes.get(s["id"], {})
        rows.append({
            "signal_id": s["id"],
            "symbol": s["symbol"],
            "score": s["score"],
            "signal_type": s["signal_type"],
            "confidence": s["confidence"],
            "created_at": s["created_at"],
            "return_1d": o.get("return_1d"),
            "return_3d": o.get("return_3d"),
            "return_5d": o.get("return_5d"),
        })
    # By signal_type
    from collections import defaultdict
    by_type: Dict[str, List[float]] = defaultdict(list)
    for r in rows:
        if r.get("return_1d") is not None:
            by_type[r["signal_type"]].append(r["return_1d"])
    summary_by_type: Dict[str, Dict[str, float]] = {}
    for st, returns in by_type.items():
        if len(returns) < 1:
            continue
        wr = sum(1 for x in returns if x > 0) / len(returns) * 100.0
        summary_by_type[st] = {
            "win_rate_1d": round(wr, 2),
            "avg_return_1d": round(sum(returns) / len(returns), 2),
            "sample_count": len(returns),
        }
    return {
        "signals_count": len(signals),
        "since": since_dt,
        "by_type": summary_by_type,
        "rows": rows,
    }


def write_backtest_csv(result: Dict[str, Any], path: Path) -> None:
    """Write backtest result rows to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = result.get("rows", [])
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    logger.info("Backtest CSV written: %s", path)


def write_backtest_report(result: Dict[str, Any], path: Path) -> None:
    """Write Markdown report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# MNEMOS 2.1 Backtest Report",
        f"Generated: {datetime.utcnow().isoformat()}Z",
        f"Signals since: {result.get('since', '')}",
        f"Total signals: {result.get('signals_count', 0)}",
        "",
        "## By signal type",
        "",
    ]
    for st, stats in result.get("by_type", {}).items():
        lines.append(f"- **{st}**: win_rate_1d={stats.get('win_rate_1d')}%, avg_return_1d={stats.get('avg_return_1d')}%, n={stats.get('sample_count')}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info("Backtest report written: %s", path)


def run_and_export_backtest(since_dt: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Run backtest and export CSV + report. Returns result dict."""
    output_dir = output_dir or REPORTS_DIR
    result = run_backtest(since_dt)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    write_backtest_csv(result, output_dir / f"backtest_{ts}.csv")
    write_backtest_report(result, output_dir / f"backtest_{ts}.md")
    return result
