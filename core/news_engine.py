"""
MNEMOS 2.0 - News engine via Google News RSS.
Parses top headlines for Indian markets / symbols.
No API key required.
"""
import logging
import re
from typing import List, Optional
from urllib.parse import quote_plus

import feedparser
import requests

logger = logging.getLogger(__name__)

# Google News RSS (region India, no API key)
GOOGLE_NEWS_INDIA = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
# Search RSS (query in q param)
GOOGLE_NEWS_SEARCH_TMPL = "https://news.google.com/rss/search?hl=en-IN&gl=IN&ceid=IN:en&q={query}"


def _fetch_rss(url: str, timeout: int = 15) -> Optional[feedparser.FeedParserDict]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Mnemos/2.0)"}
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception as e:
        logger.warning("RSS fetch failed for %s: %s", url[:60], e)
        return None


def get_top_headlines_india(max_items: int = 5) -> List[dict]:
    """
    Top India business/market headlines from Google News India.
    Returns list of {title, link, published, summary}.
    """
    feed = _fetch_rss(GOOGLE_NEWS_INDIA)
    if not feed or not feed.entries:
        return []
    out: List[dict] = []
    for e in feed.entries[:max_items]:
        title = (e.get("title") or "").strip()
        link = e.get("link") or ""
        published = e.get("published") or ""
        summary = (e.get("summary") or "")[:200].strip()
        # Strip HTML tags from summary
        summary = re.sub(r"<[^>]+>", "", summary)
        if title:
            out.append({"title": title, "link": link, "published": published, "summary": summary})
    return out


def get_headlines_for_query(query: str, max_items: int = 5) -> List[dict]:
    """Headlines for a search query (e.g. company name or symbol)."""
    url = GOOGLE_NEWS_SEARCH_TMPL.format(query=quote_plus(query))
    feed = _fetch_rss(url)
    if not feed or not feed.entries:
        return []
    out: List[dict] = []
    for e in feed.entries[:max_items]:
        title = (e.get("title") or "").strip()
        link = e.get("link") or ""
        published = e.get("published") or ""
        summary = (e.get("summary") or "")[:200].strip()
        summary = re.sub(r"<[^>]+>", "", summary)
        if title:
            out.append({"title": title, "link": link, "published": published, "summary": summary})
    return out


def get_headlines_for_symbol(symbol: str, max_items: int = 5) -> List[dict]:
    """
    Headlines for a ticker. Strips .NS and uses company name hint.
    For NSE symbols we search the base name (e.g. RELIANCE -> "Reliance India stock").
    """
    base = symbol.replace(".NS", "").replace(".BO", "").strip()
    if not base:
        return []
    query = f"{base} India stock market"
    return get_headlines_for_query(query, max_items=max_items)
