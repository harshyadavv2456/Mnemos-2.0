"""
MNEMOS 2.0 - Feature engineering for friction scoring.
Price change %, volume ratio, volatility, sector-relative strength.
"""
import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def price_change_pct(series: pd.Series, window: int = 1) -> float:
    """Return (current - past) / past * 100. NaN if insufficient data."""
    if series is None or len(series) < window + 1:
        return float("nan")
    current = series.iloc[-1]
    past = series.iloc[-(window + 1)]
    if past == 0 or np.isnan(past):
        return float("nan")
    return float((current - past) / past * 100.0)


def volume_ratio(series: pd.Series, window: int = 20) -> float:
    """Current volume / rolling mean volume. >1 = above average."""
    if series is None or len(series) < 2:
        return float("nan")
    current = series.iloc[-1]
    if current == 0:
        return 0.0
    roll = series.rolling(window, min_periods=1).mean()
    mean_vol = roll.iloc[-1]
    if mean_vol == 0:
        return float("nan")
    return float(current / mean_vol)


def volatility_pct(series: pd.Series, window: int = 10) -> float:
    """Annualized volatility proxy: std of returns over window, scaled."""
    if series is None or len(series) < 2 or window < 2:
        return float("nan")
    returns = series.pct_change().dropna()
    if len(returns) < window:
        return float("nan")
    ret_slice = returns.iloc[-window:]
    return float(ret_slice.std() * 100.0)  # as percentage


def compute_bar_features(
    df_daily: pd.DataFrame,
    symbol: str,
    lookback_days: int = 20,
) -> Dict[str, float]:
    """
    Compute features for one symbol from daily OHLCV.
    df_daily: columns Open, High, Low, Close, Volume (and symbol if multi).
    """
    if df_daily is None or df_daily.empty:
        return {}
    sub = df_daily[df_daily["symbol"] == symbol].sort_values("datetime").tail(lookback_days + 5)
    if sub.empty or "Close" not in sub.columns:
        return {}
    close = sub["Close"]
    volume = sub["Volume"] if "Volume" in sub.columns else pd.Series(dtype=float)
    if volume.empty:
        volume = pd.Series(0.0, index=close.index)
    return {
        "price_change_1d_pct": price_change_pct(close, 1),
        "price_change_5d_pct": price_change_pct(close, 5),
        "volume_ratio": volume_ratio(volume, lookback_days),
        "volatility_pct": volatility_pct(close, min(10, len(close) - 1)),
    }


def sector_relative_strength(
    symbol_returns: float,
    sector_returns: Dict[str, float],
) -> Optional[float]:
    """
    Relative strength vs sector: symbol_returns - sector_avg.
    sector_returns: dict symbol -> return. Same symbol can be in sector.
    """
    if symbol_returns != symbol_returns:  # NaN
        return None
    vals = [r for r in sector_returns.values() if r == r]
    if not vals:
        return None
    sector_avg = float(np.mean(vals))
    return float(symbol_returns - sector_avg)


def build_features_for_symbols(
    df_daily: pd.DataFrame,
    symbols: list,
    lookback_days: int = 20,
) -> Dict[str, Dict[str, float]]:
    """
    Build feature dict per symbol. Optionally add sector-relative (we use index proxy).
    """
    out: Dict[str, Dict[str, float]] = {}
    for sym in symbols:
        feats = compute_bar_features(df_daily, sym, lookback_days)
        if feats:
            out[sym] = feats
    # Simple sector proxy: relative to average 1d return of all symbols
    if out:
        avg_1d = np.nanmean([f.get("price_change_1d_pct", float("nan")) for f in out.values()])
        sector_returns = {s: f.get("price_change_1d_pct", 0.0) for s, f in out.items()}
        for sym, f in out.items():
            rel = sector_relative_strength(f.get("price_change_1d_pct", float("nan")), sector_returns)
            if rel is not None:
                f["sector_relative_1d"] = rel
    return out
