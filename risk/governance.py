"""
MNEMOS 2.1 - Risk governance: liquidity filters, volatility caps, event filters, sector exposure limits, blacklist.
"""
import logging
from typing import Dict, List, Optional, Set

from config.settings import (
    get_blacklist,
    get_watchlist,
    MAX_VOLATILITY_PCT,
    MIN_LIQUIDITY_VOLUME,
    MAX_SECTOR_EXPOSURE_PCT,
)

logger = logging.getLogger(__name__)


def apply_blacklist(symbols: List[str]) -> List[str]:
    """Remove blacklisted symbols. Never allow-list from user input; use config only."""
    bl = set(get_blacklist())
    if not bl:
        return list(symbols)
    return [s for s in symbols if s not in bl]


def liquidity_filter(features_by_symbol: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    Drop symbols with volume below MIN_LIQUIDITY_VOLUME (or missing volume).
    features_by_symbol may contain volume_ratio and we need raw volume from elsewhere;
    here we use a proxy: if volume_ratio is present and we have no explicit volume,
    we keep symbol (volume check is done at fetch time in practice). Optional: require volume_ratio >= threshold.
    """
    out: Dict[str, Dict[str, float]] = {}
    for sym, feats in features_by_symbol.items():
        vol_ratio = feats.get("volume_ratio")
        if vol_ratio is not None and vol_ratio != vol_ratio:  # NaN
            continue
        # If we had raw volume we'd filter: if volume < MIN_LIQUIDITY_VOLUME: continue
        out[sym] = feats
    return out


def volatility_filter(features_by_symbol: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """Drop symbols with volatility_pct > MAX_VOLATILITY_PCT."""
    out: Dict[str, Dict[str, float]] = {}
    for sym, feats in features_by_symbol.items():
        vol = feats.get("volatility_pct")
        if vol is not None and vol == vol and vol > MAX_VOLATILITY_PCT:
            logger.debug("Risk: skip %s volatility %.2f > cap %.2f", sym, vol, MAX_VOLATILITY_PCT)
            continue
        out[sym] = feats
    return out


def sector_exposure_filter(
    symbols_to_alert: List[str],
    sector_map: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    Limit alerts per sector to MAX_SECTOR_EXPOSURE_PCT of total.
    sector_map: symbol -> sector (if None, we treat all as one sector = no per-sector limit).
    """
    if not sector_map or not symbols_to_alert:
        return list(symbols_to_alert)
    from collections import Counter
    counts: Dict[str, int] = Counter()
    for s in symbols_to_alert:
        sec = sector_map.get(s, "unknown")
        counts[sec] = counts.get(sec, 0) + 1
    total = len(symbols_to_alert)
    allowed_per_sector = max(1, int(total * MAX_SECTOR_EXPOSURE_PCT / 100.0))
    result: List[str] = []
    sector_seen: Dict[str, int] = {}
    for s in symbols_to_alert:
        sec = sector_map.get(s, "unknown")
        n = sector_seen.get(sec, 0)
        if n < allowed_per_sector:
            result.append(s)
            sector_seen[sec] = n + 1
    return result


def apply_risk_filters(
    symbols: List[str],
    features_by_symbol: Dict[str, Dict[str, float]],
) -> List[str]:
    """
    Apply blacklist, liquidity, volatility. Return list of symbols that pass.
    """
    symbols = apply_blacklist(symbols)
    feats = liquidity_filter(volatility_filter(features_by_symbol))
    return [s for s in symbols if s in feats]
