"""
MNEMOS 2.1 - SQLite storage: prices, signals, summaries, outcomes, confidence, dedup, restarts.
Parameterized queries only; no raw input in SQL.
"""
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, List, Optional, Tuple

import pandas as pd

from config.settings import DB_PATH, DATA_DIR

logger = logging.getLogger(__name__)

# Schema version for migrations
SCHEMA_VERSION = 2


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def cursor() -> Generator[sqlite3.Cursor, None, None]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(cur: sqlite3.Cursor) -> None:
    """Create tables if not exist. Fixed schema only."""
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            dt TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL, volume REAL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prices_symbol_dt ON prices(symbol, dt)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            score REAL NOT NULL,
            explanation TEXT,
            signals_json TEXT,
            created_at TEXT NOT NULL,
            signal_type TEXT,
            confidence REAL,
            severity INTEGER
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol_created ON signals(symbol, created_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            payload TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_summaries_kind_created ON summaries(kind, created_at)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS heartbeats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_heartbeats_ts ON heartbeats(ts)")
    # ----- 2.1: outcomes (performance attribution) -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            signal_dt TEXT NOT NULL,
            price_at_signal REAL NOT NULL,
            return_1d REAL,
            return_3d REAL,
            return_5d REAL,
            outcome_1d_dt TEXT,
            outcome_3d_dt TEXT,
            outcome_5d_dt TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (signal_id) REFERENCES signals(id)
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_signal_id ON outcomes(signal_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_symbol ON outcomes(symbol)")
    # ----- 2.1: confidence history -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS confidence_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            dt TEXT NOT NULL,
            confidence REAL NOT NULL,
            friction_score REAL,
            liquidity_score REAL,
            volatility_score REAL,
            data_quality_score REAL,
            win_rate_component REAL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_confidence_symbol_dt ON confidence_history(symbol, dt)")
    # ----- 2.1: alert lock (de-dup cooldown) -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alert_lock (
            symbol TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            last_alert_ts TEXT NOT NULL,
            PRIMARY KEY (symbol, signal_type)
        )
    """)
    # ----- 2.1: restarts (watchdog) -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS restarts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            reason TEXT,
            restart_count INTEGER NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_restarts_ts ON restarts(ts)")
    # ----- 2.1: strategy versions (optimizer) -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS strategy_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version INTEGER NOT NULL,
            config_json TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            UNIQUE(name, version)
        )
    """)
    # ----- 2.1: backtest runs -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS backtest_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_version_id INTEGER,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            summary_json TEXT,
            FOREIGN KEY (strategy_version_id) REFERENCES strategy_versions(id)
        )
    """)
    # ----- 2.1: report jobs -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS report_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            sent_at TEXT,
            payload_path TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_report_jobs_kind ON report_jobs(kind)")
    _ensure_schema_version(cur, SCHEMA_VERSION)
    logger.info("Schema initialized (v%d)", SCHEMA_VERSION)


def _ensure_schema_version(cur: sqlite3.Cursor, version: int) -> None:
    cur.execute("SELECT MAX(version) FROM schema_version")
    row = cur.fetchone()
    current = (row[0] or 0)
    if current < version:
        cur.execute("INSERT INTO schema_version (version, applied_at) VALUES (?,?)",
                    (version, datetime.utcnow().isoformat() + "Z"))


def run_migrations(cur: sqlite3.Cursor) -> None:
    """Add new columns/tables for existing DBs. No user input."""
    # Add nullable columns to signals if missing (2.0 -> 2.1)
    try:
        cur.execute("ALTER TABLE signals ADD COLUMN signal_type TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE signals ADD COLUMN confidence REAL")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE signals ADD COLUMN severity INTEGER")
    except sqlite3.OperationalError:
        pass


def insert_prices(cur: sqlite3.Cursor, df: pd.DataFrame) -> int:
    """Insert OHLCV rows. df must have columns: symbol, datetime, Open, High, Low, Close, Volume."""
    if df is None or df.empty:
        return 0
    now = datetime.utcnow().isoformat() + "Z"
    count = 0
    for _, row in df.iterrows():
        sym = str(row.get("symbol", ""))[:32]
        dt = pd.Timestamp(row.get("datetime", row.get("Date", ""))).isoformat() if pd.notna(row.get("datetime", row.get("Date"))) else now
        o = float(row.get("Open", 0)) if pd.notna(row.get("Open")) else None
        h = float(row.get("High", 0)) if pd.notna(row.get("High")) else None
        l = float(row.get("Low", 0)) if pd.notna(row.get("Low")) else None
        c = float(row.get("Close", 0)) if pd.notna(row.get("Close")) else None
        v = float(row.get("Volume", 0)) if pd.notna(row.get("Volume")) else None
        cur.execute(
            "INSERT INTO prices (symbol, dt, open, high, low, close, volume, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (sym, dt, o, h, l, c, v, now),
        )
        count += 1
    return count


def insert_signal(
    cur: sqlite3.Cursor,
    symbol: str,
    score: float,
    explanation: str,
    signals_json: str = "[]",
    signal_type: Optional[str] = None,
    confidence: Optional[float] = None,
    severity: Optional[int] = None,
) -> int:
    """Insert one friction signal. Returns signal id."""
    now = datetime.utcnow().isoformat() + "Z"
    sym = str(symbol)[:32]
    cur.execute(
        """INSERT INTO signals (symbol, score, explanation, signals_json, created_at, signal_type, confidence, severity)
           VALUES (?,?,?,?,?,?,?,?)""",
        (sym, float(score), explanation[:2000] if explanation else "", signals_json[:5000] if signals_json else "[]",
         now, (signal_type or "")[:32], confidence, severity),
    )
    return cur.lastrowid or 0


def insert_summary(cur: sqlite3.Cursor, kind: str, payload: str) -> None:
    """Insert summary row."""
    now = datetime.utcnow().isoformat() + "Z"
    cur.execute("INSERT INTO summaries (kind, payload, created_at) VALUES (?,?,?)", (kind[:64], payload[:10000] if payload else "", now))


def insert_heartbeat(cur: sqlite3.Cursor, status: str, message: Optional[str] = None) -> None:
    """Log heartbeat."""
    now = datetime.utcnow().isoformat() + "Z"
    cur.execute("INSERT INTO heartbeats (ts, status, message) VALUES (?,?,?)", (now, status[:64], (message or "")[:500]))


def insert_outcome(
    cur: sqlite3.Cursor,
    signal_id: int,
    symbol: str,
    signal_dt: str,
    price_at_signal: float,
    return_1d: Optional[float] = None,
    return_3d: Optional[float] = None,
    return_5d: Optional[float] = None,
    outcome_1d_dt: Optional[str] = None,
    outcome_3d_dt: Optional[str] = None,
    outcome_5d_dt: Optional[str] = None,
) -> None:
    """Insert performance outcome for a signal."""
    now = datetime.utcnow().isoformat() + "Z"
    cur.execute(
        """INSERT INTO outcomes (signal_id, symbol, signal_dt, price_at_signal, return_1d, return_3d, return_5d,
           outcome_1d_dt, outcome_3d_dt, outcome_5d_dt, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (signal_id, symbol[:32], signal_dt, price_at_signal, return_1d, return_3d, return_5d,
         outcome_1d_dt, outcome_3d_dt, outcome_5d_dt, now),
    )


def insert_confidence(
    cur: sqlite3.Cursor,
    symbol: str,
    dt: str,
    confidence: float,
    friction_score: Optional[float] = None,
    liquidity_score: Optional[float] = None,
    volatility_score: Optional[float] = None,
    data_quality_score: Optional[float] = None,
    win_rate_component: Optional[float] = None,
) -> None:
    """Insert confidence history row."""
    now = datetime.utcnow().isoformat() + "Z"
    cur.execute(
        """INSERT INTO confidence_history (symbol, dt, confidence, friction_score, liquidity_score,
           volatility_score, data_quality_score, win_rate_component, created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (symbol[:32], dt, confidence, friction_score, liquidity_score, volatility_score, data_quality_score, win_rate_component, now),
    )


def upsert_alert_lock(cur: sqlite3.Cursor, symbol: str, signal_type: str) -> None:
    """Set last alert time for (symbol, signal_type)."""
    now = datetime.utcnow().isoformat() + "Z"
    cur.execute(
        "INSERT OR REPLACE INTO alert_lock (symbol, signal_type, last_alert_ts) VALUES (?,?,?)",
        (symbol[:32], signal_type[:32], now),
    )


def get_alert_lock(cur: sqlite3.Cursor, symbol: str, signal_type: str) -> Optional[str]:
    """Return last_alert_ts for (symbol, signal_type) or None."""
    cur.execute("SELECT last_alert_ts FROM alert_lock WHERE symbol = ? AND signal_type = ?", (symbol[:32], signal_type[:32]))
    row = cur.fetchone()
    return row[0] if row else None


def insert_restart(cur: sqlite3.Cursor, reason: str, restart_count: int) -> None:
    """Log a restart event."""
    now = datetime.utcnow().isoformat() + "Z"
    cur.execute("INSERT INTO restarts (ts, reason, restart_count) VALUES (?,?,?)", (now, reason[:200], restart_count))


def get_restart_count_since(cur: sqlite3.Cursor, since_ts: str) -> int:
    """Count restarts since given ISO ts."""
    cur.execute("SELECT COUNT(*) FROM restarts WHERE ts >= ?", (since_ts,))
    row = cur.fetchone()
    return row[0] if row else 0


def init_db() -> None:
    """Create DB and schema; run migrations."""
    ensure_data_dir()
    with cursor() as cur:
        init_schema(cur)
        run_migrations(cur)
