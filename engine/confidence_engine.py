"""
MNEMOS 2.1 - Confidence engine: composite from friction, liquidity, volatility, data quality, historical win rate.
Only alert above threshold. Persist confidence history.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from config.settings import (
    CONFIDENCE_ALERT_THRESHOLD,
    CONFIDENCE_MIN_SAMPLES_FOR_WINRATE,
)
from analytics.attribution import get_attribution_stats
from storage.db import cursor, insert_confidence

logger = logging.getLogger(__name__)


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def liquidity_score(feats: Dict[str, float]) -> float:
    """Higher volume_ratio (up to a cap) = better liquidity. 0-1."""
    vr = feats.get("volume_ratio")
    if vr is None or vr != vr:
        return 0.5  # unknown
    if vr <= 0:
        return 0.0
    return _clip(vr / 2.0)  # 2x vol => 1.0


def volatility_score(feats: Dict[str, float]) -> float:
    """Lower volatility = higher score (less risky). 0-1."""
    v = feats.get("volatility_pct")
    if v is None or v != v:
        return 0.5
    if v <= 0:
        return 1.0
    return _clip(1.0 - v / 20.0)  # 20% vol => 0


def data_quality_score(feats: Dict[str, float]) -> float:
    """Presence of key fields and non-NaN => 1. Else lower."""
    keys = ["price_change_1d_pct", "volume_ratio", "volatility_pct"]
    n = sum(1 for k in keys if k in feats and feats[k] == feats[k])
    return n / len(keys) if keys else 0.0


def win_rate_component(symbol: Optional[str] = None) -> float:
    """Historical win rate from outcomes (1d). 0-1. Returns 0.5 if insufficient samples."""
    stats = get_attribution_stats(symbol=symbol, min_samples=CONFIDENCE_MIN_SAMPLES_FOR_WINRATE)
    wr = stats.get("win_rate_1d")
    if wr is None:
        return 0.5
    return _clip(wr / 100.0)


def compute_confidence(
    symbol: str,
    friction_score: float,
    feats: Dict[str, float],
    dt: Optional[str] = None,
) -> float:
    """
    Composite confidence: weighted sum of friction, liquidity, volatility, data quality, win rate.
    Returns 0-1. Persists to confidence_history.
    """
    dt = dt or datetime.utcnow().isoformat() + "Z"
    liq = liquidity_score(feats)
    vol = volatility_score(feats)
    dq = data_quality_score(feats)
    wr = win_rate_component(symbol)
    # Weights: friction primary, then liquidity/data quality, volatility (risk), win rate
    confidence = (
        0.35 * _clip(friction_score)
        + 0.15 * liq
        + 0.15 * vol
        + 0.15 * dq
        + 0.20 * wr
    )
    confidence = _clip(confidence)
    try:
        with cursor() as cur:
            insert_confidence(
                cur,
                symbol=symbol,
                dt=dt,
                confidence=confidence,
                friction_score=friction_score,
                liquidity_score=liq,
                volatility_score=vol,
                data_quality_score=dq,
                win_rate_component=wr,
            )
    except Exception as e:
        logger.warning("Failed to persist confidence: %s", e)
    return round(confidence, 3)


def should_alert_by_confidence(confidence: float) -> bool:
    """True if confidence >= threshold."""
    return confidence >= CONFIDENCE_ALERT_THRESHOLD
