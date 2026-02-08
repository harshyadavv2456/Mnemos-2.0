"""
MNEMOS 2.0 - Telegram bot alerts. Rich formatted messages, rate limiting.
"""
import logging
import time
from typing import Dict, Optional

from config.settings import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_MIN_INTERVAL_SEC,
    MAX_ALERTS_PER_SYMBOL_PER_HOUR,
)

logger = logging.getLogger(__name__)

_last_sent: float = 0
_per_symbol_count: Dict[str, list] = {}  # symbol -> list of timestamps


def _rate_limit_global() -> bool:
    global _last_sent
    now = time.time()
    if now - _last_sent < TELEGRAM_MIN_INTERVAL_SEC:
        return False
    _last_sent = now
    return True


def _rate_limit_symbol(symbol: str) -> bool:
    now = time.time()
    cutoff = now - 3600  # 1 hour
    if symbol not in _per_symbol_count:
        _per_symbol_count[symbol] = []
    _per_symbol_count[symbol] = [t for t in _per_symbol_count[symbol] if t > cutoff]
    if len(_per_symbol_count[symbol]) >= MAX_ALERTS_PER_SYMBOL_PER_HOUR:
        return False
    _per_symbol_count[symbol].append(now)
    return True


def send_telegram(text: str, parse_mode: str = "HTML") -> bool:
    """Send one message. Returns True if sent. Rate-limited."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.debug("Telegram not configured; skip")
        return False
    if not _rate_limit_global():
        logger.debug("Telegram rate limit (global); skip")
        return False
    try:
        import urllib.request
        import urllib.parse
        import json
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        body = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text[:4096],
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        data = urllib.parse.urlencode(body).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status == 200:
                return True
            logger.warning("Telegram API status %s", r.status)
            return False
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)
        return False


def format_friction_alert(
    symbol: str,
    score: float,
    explanation: str,
    headline: Optional[str] = None,
    groq_analysis: Optional[str] = None,
) -> str:
    """Rich Telegram message for friction signal."""
    sym_clean = symbol.replace(".NS", "").replace("^", "")
    lines = [
        f"<b>MNEMOS 2.1 – Friction</b>",
        f"<b>{sym_clean}</b>",
        f"Score: {score:.2f}",
        "",
        explanation[:500],
    ]
    if headline:
        lines.append(f"<i>{headline[:100]}</i>")
    if groq_analysis:
        lines.append(f"\n<b>AI:</b> {groq_analysis[:200]}")
    return "\n".join(lines)


def send_friction_alert(
    symbol: str,
    score: float,
    explanation: str,
    headline: Optional[str] = None,
    groq_analysis: Optional[str] = None,
) -> bool:
    """Send friction alert if Telegram configured and rate limit allows (per-symbol)."""
    if not _rate_limit_symbol(symbol):
        logger.debug("Telegram rate limit (symbol %s); skip", symbol)
        return False
    msg = format_friction_alert(symbol, score, explanation, headline, groq_analysis)
    return send_telegram(msg)
