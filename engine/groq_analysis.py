"""
MNEMOS 2.1 - GROQ API (free Llama) analysis on signal/market data.
Uses GROQ_API_KEY; rate-limited to preserve free tier.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from config.settings import GROQ_API_KEY, GROQ_MODEL, GROQ_MAX_DAILY_CALLS

logger = logging.getLogger(__name__)

_call_times: list = []
_calls_today: int = 0
_last_date: Optional[str] = None


def _rate_limit() -> bool:
    """True if we can make a call (under daily limit)."""
    global _calls_today, _last_date
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if _last_date != today:
        _last_date = today
        _calls_today = 0
    if _calls_today >= GROQ_MAX_DAILY_CALLS:
        return False
    return True


def get_analysis(prompt: str, max_tokens: int = 256) -> Optional[str]:
    """
    Call GROQ with Llama model. Returns analysis text or None on failure/rate limit.
    Prompt should be short; response is truncated to max_tokens.
    """
    if not GROQ_API_KEY or not prompt.strip():
        return None
    if not _rate_limit():
        logger.debug("GROQ daily limit reached; skip")
        return None
    try:
        import urllib.request
        import json
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt[:2000]}],
            "max_tokens": max(50, min(max_tokens, 512)),
            "temperature": 0.3,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status != 200:
                logger.warning("GROQ API status %s", r.status)
                return None
            out = json.loads(r.read().decode())
        global _calls_today
        _calls_today += 1
        choices = out.get("choices", [])
        if not choices:
            return None
        text = (choices[0].get("message") or {}).get("content", "").strip()
        return text[:500] if text else None
    except Exception as e:
        logger.warning("GROQ request failed: %s", e)
        return None


def analyze_signal(symbol: str, score: float, explanation: str) -> Optional[str]:
    """One-line LLM take on a friction signal for inclusion in alerts."""
    prompt = (
        f"In one short sentence (under 25 words), what might this Indian market signal mean for a trader? "
        f"Symbol: {symbol}, Friction score: {score:.2f}. Context: {explanation[:200]}"
    )
    return get_analysis(prompt, max_tokens=80)
