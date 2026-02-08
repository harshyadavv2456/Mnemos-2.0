"""
MNEMOS 2.0 - OHLCV data fetcher via yfinance.
Pulls every N minutes; supports multiple NSE symbols.
Indian markets: use .NS suffix.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def fetch_ohlcv(
    symbols: List[str],
    period: str = "1d",
    interval: str = "5m",
) -> pd.DataFrame:
    """
    Fetch OHLCV for given symbols. Retries on failure.
    period: 1d, 5d, etc. interval: 1m, 5m, 15m, 1h, 1d.
    """
    if not symbols:
        return pd.DataFrame()
    try:
        tickers = yf.Tickers(" ".join(symbols))
        frames: List[pd.DataFrame] = []
        for sym in symbols:
            try:
                t = tickers.tickers.get(sym) or yf.Ticker(sym)
                hist = t.history(period=period, interval=interval, auto_adjust=True)
                if hist is not None and not hist.empty:
                    hist = hist.reset_index()
                    hist["symbol"] = sym
                    frames.append(hist)
            except Exception as e:
                logger.warning("Fetch failed for %s: %s", sym, e)
                continue
        if not frames:
            return pd.DataFrame()
        out = pd.concat(frames, ignore_index=True)
        if "Date" in out.columns:
            out["datetime"] = pd.to_datetime(out["Date"]).dt.tz_localize(None)
        return out
    except Exception as e:
        logger.error("fetch_ohlcv failed: %s", e)
        raise


def fetch_latest_bars(
    symbols: List[str],
    interval_min: int = 5,
) -> pd.DataFrame:
    """
    Fetch latest intraday bars (today). For 3-min monitoring we use 5m granularity.
    """
    return fetch_ohlcv(symbols, period="1d", interval="5m")


def fetch_daily_for_features(
    symbols: List[str],
    days: int = 30,
) -> pd.DataFrame:
    """Daily OHLCV for feature engineering (volatility, volume ratio, etc.)."""
    return fetch_ohlcv(symbols, period=f"{days}d", interval="1d")
