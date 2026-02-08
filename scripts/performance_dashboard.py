#!/usr/bin/env python3
"""
MNEMOS 2.1 - Performance dashboard: print attribution stats, recent signals, heartbeats.
Run: python scripts/performance_dashboard.py [--json]
"""
import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from analytics.attribution import get_attribution_stats
from storage.db import cursor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    stats = get_attribution_stats(min_samples=0)
    with cursor() as cur:
        cur.execute(
            "SELECT symbol, score, confidence, signal_type, created_at FROM signals ORDER BY created_at DESC LIMIT 20"
        )
        signals = [dict(zip(["symbol", "score", "confidence", "signal_type", "created_at"], row)) for row in cur.fetchall()]
        cur.execute(
            "SELECT ts, status, message FROM heartbeats ORDER BY ts DESC LIMIT 10"
        )
        heartbeats = [dict(zip(["ts", "status", "message"], row)) for row in cur.fetchall()]

    out = {
        "attribution": stats,
        "recent_signals": signals,
        "recent_heartbeats": heartbeats,
    }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print("=== MNEMOS 2.1 Performance Dashboard ===\n")
        print("Attribution:", json.dumps(stats, indent=2))
        print("\nRecent signals (20):", json.dumps(signals, indent=2))
        print("\nRecent heartbeats (10):", json.dumps(heartbeats, indent=2))


if __name__ == "__main__":
    main()
