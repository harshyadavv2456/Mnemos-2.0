"""
MNEMOS 2.0 - Friction scoring engine.
Detects: panic selling, silent accumulation, sector lag, news underreaction, overreaction.
Returns score [0,1] + explanation.
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from core.feature_engineering import build_features_for_symbols
from core.news_engine import get_headlines_for_symbol

logger = logging.getLogger(__name__)


@dataclass
class FrictionResult:
    """Friction score and human-readable explanation."""
    symbol: str
    score: float  # 0..1, higher = more friction/opportunity
    explanation: str
    signals: List[str]
    signal_type: str = "unknown"  # panic_selling, silent_accumulation, sector_lag, news_underreaction, overreaction


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def _panic_selling_score(feats: Dict[str, float]) -> tuple[float, List[str]]:
    """
    Large negative return + high volume => panic selling.
    """
    out: List[str] = []
    ret_1d = feats.get("price_change_1d_pct", 0.0)
    vol_ratio = feats.get("volume_ratio", 0.0)
    if ret_1d != ret_1d or vol_ratio != vol_ratio:
        return 0.0, out
    # Panic: down >2% and volume >1.5x
    if ret_1d < -2.0 and vol_ratio > 1.5:
        s = _clip(0.3 + abs(ret_1d) / 50.0 + (vol_ratio - 1.0) / 4.0)
        out.append(f"Panic selling: {ret_1d:.2f}% drop, vol {vol_ratio:.2f}x avg")
        return _clip(s), out
    return 0.0, out


def _silent_accumulation_score(feats: Dict[str, float]) -> tuple[float, List[str]]:
    """
    Price up slightly + low volume => accumulation.
    """
    out: List[str] = []
    ret_1d = feats.get("price_change_1d_pct", 0.0)
    ret_5d = feats.get("price_change_5d_pct", 0.0)
    vol_ratio = feats.get("volume_ratio", 0.0)
    if ret_1d != ret_1d:
        return 0.0, out
    if 0 < ret_1d < 1.5 and (vol_ratio != vol_ratio or vol_ratio < 0.8):
        out.append(f"Silent accumulation: +{ret_1d:.2f}% on below-avg volume")
        return _clip(0.4 + ret_5d / 50.0 if ret_5d == ret_5d else 0.4), out
    return 0.0, out


def _sector_lag_score(feats: Dict[str, float]) -> tuple[float, List[str]]:
    """
    Sector relative strength negative => lagging sector.
    """
    out: List[str] = []
    rel = feats.get("sector_relative_1d", 0.0)
    if rel != rel:
        return 0.0, out
    if rel < -1.0:
        out.append(f"Sector lag: {rel:.2f}% vs peers")
        return _clip(0.3 + abs(rel) / 30.0), out
    return 0.0, out


def _news_underreaction_score(
    symbol: str,
    feats: Dict[str, float],
    headlines: List[dict],
) -> tuple[float, List[str]]:
    """
    Recent negative news but price not down much => underreaction.
    Simplified: if we have notable headlines and small move, score.
    """
    out: List[str] = []
    if not headlines:
        return 0.0, out
    ret_1d = feats.get("price_change_1d_pct", 0.0)
    if ret_1d != ret_1d:
        return 0.0, out
    # Heuristic: news exists, price move < 1% => possible underreaction
    if abs(ret_1d) < 1.0 and len(headlines) >= 1:
        titles = [h.get("title", "")[:60] for h in headlines[:2]]
        out.append("News vs price: limited move despite headlines")
        for t in titles:
            if t:
                out.append(f"  • {t}")
        return 0.35, out
    return 0.0, out


def _overreaction_score(feats: Dict[str, float]) -> tuple[float, List[str]]:
    """
    Large single-day move (up or down) + high volatility => overreaction.
    """
    out: List[str] = []
    ret_1d = feats.get("price_change_1d_pct", 0.0)
    vol_pct = feats.get("volatility_pct", 0.0)
    if ret_1d != ret_1d:
        return 0.0, out
    if abs(ret_1d) > 4.0:
        out.append(f"Overreaction: {ret_1d:.2f}% in 1d")
        s = 0.3 + min(abs(ret_1d) / 25.0, 0.4)
        if vol_pct == vol_pct and vol_pct > 2.0:
            s += 0.1
        return _clip(s), out
    return 0.0, out


def compute_friction(
    symbol: str,
    feats: Dict[str, float],
    headlines: Optional[List[dict]] = None,
) -> FrictionResult:
    """
    Compute single friction score and explanation for one symbol.
    """
    headlines = headlines or get_headlines_for_symbol(symbol, max_items=3)
    all_signals: List[str] = []
    scores: List[float] = []

    s1, sig1 = _panic_selling_score(feats)
    if s1 > 0:
        scores.append(s1)
        all_signals.extend(sig1)

    s2, sig2 = _silent_accumulation_score(feats)
    if s2 > 0:
        scores.append(s2)
        all_signals.extend(sig2)

    s3, sig3 = _sector_lag_score(feats)
    if s3 > 0:
        scores.append(s3)
        all_signals.extend(sig3)

    s4, sig4 = _news_underreaction_score(symbol, feats, headlines)
    if s4 > 0:
        scores.append(s4)
        all_signals.extend(sig4)

    s5, sig5 = _overreaction_score(feats)
    if s5 > 0:
        scores.append(s5)
        all_signals.extend(sig5)

    if not scores:
        return FrictionResult(
            symbol=symbol,
            score=0.0,
            explanation="No friction signals detected.",
            signals=[],
            signal_type="unknown",
        )
    # Combined: take max and add small bonus for multiple signals
    combined = min(1.0, max(scores) + 0.05 * (len(scores) - 1))
    explanation = " | ".join(all_signals) if all_signals else "Friction signals present."
    from alerts.dedup import infer_signal_type
    signal_type = infer_signal_type(all_signals)
    return FrictionResult(
        symbol=symbol,
        score=round(combined, 3),
        explanation=explanation,
        signals=all_signals,
        signal_type=signal_type,
    )


def compute_friction_batch(
    features_by_symbol: Dict[str, Dict[str, float]],
    fetch_news: bool = True,
) -> List[FrictionResult]:
    """
    Compute friction for all symbols with features.
    Optionally fetch news per symbol (rate-limited by caller).
    """
    results: List[FrictionResult] = []
    for symbol, feats in features_by_symbol.items():
        headlines = get_headlines_for_symbol(symbol, max_items=3) if fetch_news else None
        try:
            r = compute_friction(symbol, feats, headlines)
            results.append(r)
        except Exception as e:
            logger.warning("Friction compute failed for %s: %s", symbol, e)
            results.append(FrictionResult(symbol=symbol, score=0.0, explanation=str(e), signals=[], signal_type="unknown"))
    return results
