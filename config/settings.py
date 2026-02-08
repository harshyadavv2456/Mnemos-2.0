"""
MNEMOS 2.1 - Central configuration.
Loads from .env; no secrets in code. Indian markets only (NSE: .NS).
Minimum 150 stocks by market cap (decreasing).
"""
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load .env from project root (or Colab env)
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

# ----- Paths -----
DATA_DIR = Path(os.getenv("MNEMOS_DATA_DIR", str(_ROOT / "data")))
DB_PATH = DATA_DIR / "mnemos.db"
BACKUP_DIR = Path(os.getenv("MNEMOS_BACKUP_DIR", str(DATA_DIR / "backups")))
LOG_DIR = Path(os.getenv("MNEMOS_LOG_DIR", str(_ROOT / "logs")))
REPORTS_DIR = Path(os.getenv("MNEMOS_REPORTS_DIR", str(_ROOT / "reports")))

# ----- Market: Indian (NSE) -----
NSE_SUFFIX = ".NS"
# Default watchlist: 150+ stocks by market cap (decreasing) - Nifty 50 + Next 50 + liquid mid/large
_RAW_WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "HCLTECH.NS",
    "WIPRO.NS", "TITAN.NS", "SUNPHARMA.NS", "BAJFINANCE.NS", "ULTRACEMCO.NS",
    "NESTLEIND.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "POWERGRID.NS", "NTPC.NS",
    "ONGC.NS", "INDUSINDBK.NS", "TECHM.NS", "ADANIPORTS.NS", "CIPLA.NS",
    "DRREDDY.NS", "BRITANNIA.NS", "DIVISLAB.NS", "GRASIM.NS", "HINDALCO.NS",
    "JSWSTEEL.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "APOLLOHOSP.NS", "BAJAJ-AUTO.NS",
    "COALINDIA.NS", "M&M.NS", "SHRIRAMFIN.NS", "TATACONSUM.NS", "HDFCLIFE.NS",
    "SBILIFE.NS", "PIDILITIND.NS", "ADANIENT.NS", "LTIM.NS", "BEL.NS",
    "SIEMENS.NS", "HAL.NS", "MARICO.NS", "BANKBARODA.NS", "CANBK.NS",
    "PNB.NS", "UNIONBANK.NS", "IDEA.NS", "VEDL.NS", "DABUR.NS",
    "BOSCHLTD.NS", "HAVELLS.NS", "ABB.NS", "TATAPOWER.NS", "AMBUJACEM.NS",
    "ACC.NS", "GAIL.NS", "IOC.NS", "BPCL.NS", "HINDPETRO.NS",
    "RECLTD.NS", "PFC.NS", "BHEL.NS", "SRF.NS", "AUROPHARMA.NS",
    "TORNTPHARM.NS", "LALPATHLAB.NS", "METROPOLIS.NS", "BIOCON.NS", "GLENMARK.NS",
    "CADILAHC.NS", "MANAPPURAM.NS", "MUTHOOTFIN.NS", "CHOLAFIN.NS", "BAJAJFINSV.NS",
    "ICICIPRULI.NS", "HDFCAMC.NS", "SBICARD.NS", "PIIND.NS", "AARTIIND.NS",
    "ATUL.NS", "AEGISLOG.NS", "ALKEM.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS",
    "ASTRAL.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS",
    "BERGEPAINT.NS", "BATAINDIA.NS", "CONCOR.NS", "CUMMINSIND.NS", "DALBHARAT.NS",
    "DEEPAKNTR.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "FINCABLES.NS",
    "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS", "GRANULES.NS",
    "GUJGASLTD.NS", "HAPPIESTMIN.NS", "ICICIGI.NS", "IDFC.NS", "IDFCFIRSTB.NS",
    "IGL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", "IRCTC.NS",
    "JKCEMENT.NS", "JINDALSTEL.NS", "JSWENERGY.NS", "JUBLFOOD.NS",
    "LAURUSLABS.NS", "LICHSGFIN.NS", "LUPIN.NS", "MRF.NS", "MOTHERSON.NS",
    "MPHASIS.NS", "NATIONALUM.NS", "NAUKRI.NS", "NAVINFLUOR.NS", "OBEROIRLTY.NS",
    "OFSS.NS", "PAGEIND.NS", "PEL.NS", "PERSISTENT.NS", "PETRONET.NS",
    "POLYCAB.NS", "RAMCOCEM.NS", "RATNAMANI.NS", "SAIL.NS", "SANOFI.NS",
    "SHREECEM.NS", "SRTRANSFIN.NS", "SUNTV.NS", "SYNGENE.NS", "TATACOMM.NS",
    "TATATECH.NS", "TRENT.NS", "UPL.NS", "VOLTAS.NS", "WHIRLPOOL.NS",
    "ZYDUSLIFE.NS", "ADANIGREEN.NS", "ADANITRANS.NS", "ABCAPITAL.NS", "ABFRL.NS",
    "AUBANK.NS", "COFORGE.NS", "FORTIS.NS", "GODREJIND.NS",
    "HATSUN.NS", "IPCALAB.NS", "KEI.NS", "MAHABANK.NS", "MAXHEALTH.NS",
    "MCX.NS", "NYKAA.NS", "PATANJALI.NS", "POLICYBZR.NS", "RVNL.NS",
    "SUPREMEIND.NS", "TATACHEM.NS", "TATAELXSI.NS", "TVSMOTOR.NS",
    "COLPAL.NS", "DIXON.NS", "ENDURANCE.NS", "FACT.NS", "FSN-E.NS",
    "HONAUT.NS", "IIFL.NS", "KAJARIACER.NS", "LTIINFRA.NS", "MAHSCOOTER.NS",
    "NMDC.NS", "OIL.NS", "PPLPHARMA.NS", "QUESS.NS", "RAJESHEXPO.NS",
    "SKFINDIA.NS", "TECHNOE.NS", "UCOBANK.NS", "VAKRANGEE.NS", "WABCOINDIA.NS",
]
# Indian indices (Yahoo: ^NSEI etc.) and commodities (Gold/Silver ETFs on NSE)
INDICES_AND_COMMODITIES: List[str] = [
    "^NSEI",   # Nifty 50
    "^BSESN",  # Sensex
    "^NSEBANK",  # Bank Nifty
    "^CNXIT",  # Nifty IT
    "GOLDBEES.NS",   # Gold ETF (India)
    "GOLDSHARE.NS",  # Gold ETF
    "SILVERETFS.NS", # Silver ETF (India)
]
DEFAULT_WATCHLIST: List[str] = list(dict.fromkeys(_RAW_WATCHLIST + INDICES_AND_COMMODITIES))


def _normalize_symbol(s: str) -> str:
    """Index (^...) or already .NS stays as-is; else add .NS."""
    s = s.strip().upper()
    if not s:
        return s
    if s.startswith("^") or s.endswith(".NS") or s.endswith(".BO"):
        return s
    return f"{s}.NS"


def get_watchlist() -> List[str]:
    """Watchlist from env (comma-separated) or default. Indices (^...) and .NS preserved."""
    raw = os.getenv("MNEMOS_WATCHLIST", "").strip()
    if raw:
        symbols = [s.strip() for s in raw.split(",") if s.strip()]
        return [_normalize_symbol(s) for s in symbols]
    return list(DEFAULT_WATCHLIST)


# ----- Alerts -----
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
# Comma-separated for mail trail (all get same update; anyone can add others via reply)
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", GMAIL_USER or "")

# GROQ API (free tier ~1600 req/day) for Llama analysis on signals
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_MAX_DAILY_CALLS = max(1, int(os.getenv("GROQ_MAX_DAILY_CALLS", "100")))

# ----- Rate limiting -----
TELEGRAM_MIN_INTERVAL_SEC = max(1, int(os.getenv("TELEGRAM_MIN_INTERVAL_SEC", "60")))
EMAIL_MIN_INTERVAL_SEC = max(60, int(os.getenv("EMAIL_MIN_INTERVAL_SEC", "300")))
MAX_ALERTS_PER_SYMBOL_PER_HOUR = max(1, int(os.getenv("MAX_ALERTS_PER_SYMBOL_PER_HOUR", "3")))

# ----- Signal de-dup -----
SIGNAL_COOLDOWN_MINUTES = max(0, int(os.getenv("SIGNAL_COOLDOWN_MINUTES", "60")))
ALERT_COOLDOWN_SYMBOL_MINUTES = max(0, int(os.getenv("ALERT_COOLDOWN_SYMBOL_MINUTES", "120")))

# ----- Polling -----
POLL_INTERVAL_MARKET_MIN = max(1, int(os.getenv("POLL_INTERVAL_MARKET_MIN", "3")))
POLL_INTERVAL_OFF_MIN = max(5, int(os.getenv("POLL_INTERVAL_OFF_MIN", "30")))

# ----- Market hours (IST) -----
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MIN = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MIN = 30

# ----- Friction & confidence -----
FRICTION_ALERT_THRESHOLD = float(os.getenv("FRICTION_ALERT_THRESHOLD", "0.65"))
CONFIDENCE_ALERT_THRESHOLD = float(os.getenv("CONFIDENCE_ALERT_THRESHOLD", "0.60"))
CONFIDENCE_MIN_SAMPLES_FOR_WINRATE = max(5, int(os.getenv("CONFIDENCE_MIN_SAMPLES_FOR_WINRATE", "20")))

# ----- Risk governance -----
MIN_LIQUIDITY_VOLUME = float(os.getenv("MIN_LIQUIDITY_VOLUME", "100000"))
MAX_VOLATILITY_PCT = float(os.getenv("MAX_VOLATILITY_PCT", "15.0"))
MAX_SECTOR_EXPOSURE_PCT = float(os.getenv("MAX_SECTOR_EXPOSURE_PCT", "25.0"))
RISK_BLACKLIST_ENV = os.getenv("MNEMOS_BLACKLIST", "")  # comma-separated symbols

# ----- Health & watchdog -----
DAILY_HEARTBEAT_HOUR_UTC = int(os.getenv("DAILY_HEARTBEAT_HOUR_UTC", "4"))
WATCHDOG_MAX_MEMORY_MB = float(os.getenv("WATCHDOG_MAX_MEMORY_MB", "2048"))
WATCHDOG_MAX_RESTARTS_PER_HOUR = max(1, int(os.getenv("WATCHDOG_MAX_RESTARTS_PER_HOUR", "5")))
SUPERVISOR_RESTART_DELAY_SEC = max(5, int(os.getenv("SUPERVISOR_RESTART_DELAY_SEC", "30")))

# ----- Drive backup -----
DRIVE_BACKUP_FOLDER_NAME = os.getenv("DRIVE_BACKUP_FOLDER_NAME", "mnemos_backups")

# ----- Reporting -----
WEEKLY_REPORT_DAY = int(os.getenv("WEEKLY_REPORT_DAY", "0"))  # 0=Monday
MONTHLY_REPORT_DAY = max(1, min(28, int(os.getenv("MONTHLY_REPORT_DAY", "1"))))

# ----- Logging -----
LOG_LEVEL = os.getenv("MNEMOS_LOG_LEVEL", "INFO")


def get_blacklist() -> List[str]:
    """Symbol blacklist from env. Ensures .NS."""
    raw = (RISK_BLACKLIST_ENV or "").strip()
    if not raw:
        return []
    symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]
    return [s if s.endswith(".NS") else f"{s}.NS" for s in symbols]
