"""
MNEMOS 2.1 - Strategy optimizer: auto-tune thresholds, promote high-performing rules, deprecate weak rules, version strategies.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from analytics.attribution import get_attribution_stats
from storage.db import cursor

logger = logging.getLogger(__name__)


def get_active_strategy_config() -> Optional[Dict[str, Any]]:
    """Load active strategy version config (JSON)."""
    with cursor() as cur:
        cur.execute(
            "SELECT config_json FROM strategy_versions WHERE active = 1 ORDER BY created_at DESC LIMIT 1"
        )
        row = cur.fetchone()
    if not row or not row[0]:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


def save_strategy_version(name: str, config: Dict[str, Any], active: bool = True) -> int:
    """Save new strategy version. Returns version id."""
    with cursor() as cur:
        cur.execute(
            "SELECT COALESCE(MAX(version), 0) + 1 FROM strategy_versions WHERE name = ?",
            (name[:64],),
        )
        ver = cur.fetchone()[0] or 1
        now = datetime.utcnow().isoformat() + "Z"
        cur.execute(
            "UPDATE strategy_versions SET active = 0 WHERE name = ?",
            (name[:64],),
        )
        cur.execute(
            "INSERT INTO strategy_versions (name, version, config_json, active, created_at) VALUES (?,?,?,?,?)",
            (name[:64], ver, json.dumps(config)[:10000], 1 if active else 0, now),
        )
        return cur.lastrowid or 0


def suggest_thresholds() -> Dict[str, float]:
    """
    Suggest friction/confidence thresholds from recent win rate.
    If win_rate_1d > 55% suggest same or slightly lower threshold; else raise.
    """
    stats = get_attribution_stats(min_samples=10)
    wr = stats.get("win_rate_1d") or 50.0
    avg = stats.get("avg_return_1d") or 0.0
    # Heuristic
    if wr >= 60 and avg > 0:
        return {"friction_threshold": 0.60, "confidence_threshold": 0.55}
    if wr >= 55:
        return {"friction_threshold": 0.65, "confidence_threshold": 0.60}
    if wr < 45:
        return {"friction_threshold": 0.72, "confidence_threshold": 0.65}
    return {"friction_threshold": 0.65, "confidence_threshold": 0.60}


def rank_rules_by_performance() -> List[Dict[str, Any]]:
    """
    Rank signal types by win rate (from outcomes joined to signals.signal_type).
    Returns list of {signal_type, win_rate_1d, sample_count}.
    """
    with cursor() as cur:
        cur.execute("""
            SELECT s.signal_type, o.return_1d
            FROM outcomes o
            JOIN signals s ON s.id = o.signal_id
            WHERE o.return_1d IS NOT NULL AND s.signal_type IS NOT NULL AND s.signal_type != ''
        """)
        rows = cur.fetchall()
    from collections import defaultdict
    by_type: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        by_type[row[0]].append(float(row[1]))
    result: List[Dict[str, Any]] = []
    for sig_type, returns in by_type.items():
        if len(returns) < 5:
            continue
        wr = sum(1 for r in returns if r > 0) / len(returns) * 100.0
        avg = sum(returns) / len(returns)
        result.append({
            "signal_type": sig_type,
            "win_rate_1d": round(wr, 2),
            "avg_return_1d": round(avg, 2),
            "sample_count": len(returns),
        })
    result.sort(key=lambda x: (x["win_rate_1d"], x["sample_count"]), reverse=True)
    return result
