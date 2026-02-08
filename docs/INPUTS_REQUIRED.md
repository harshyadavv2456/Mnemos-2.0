# MNEMOS 2.1 – Inputs Required From You

To run MNEMOS 2.1 on Colab **24/7** (until the free session disconnects), you only need to provide the following. Everything else has defaults.

---

## Required for alerts and daily heartbeat

| What | Where to set | How to get it |
|------|----------------|----------------|
| **TELEGRAM_BOT_TOKEN** | Colab env cell or Colab Secrets | Telegram → @BotFather → /newbot → copy token |
| **TELEGRAM_CHAT_ID** | Colab env cell or Colab Secrets | Telegram → @userinfobot → send any message → copy numeric ID |
| **GMAIL_USER** | Colab env or Secrets | Your Gmail address |
| **GMAIL_APP_PASSWORD** | Colab env or Secrets | Google Account → Security → 2-Step Verification → App passwords → generate for "Mail" |
| **ALERT_EMAIL_TO** | Colab env or Secrets | Same as GMAIL_USER (or another address for reports) |

Without these, the system still runs and logs to the notebook/DB, but **no Telegram or email alerts** and **no daily heartbeat** will be sent.

---

## Optional (defaults are fine)

| What | Default | When to set |
|------|---------|-------------|
| **MNEMOS_WATCHLIST** | 150+ NSE stocks by market cap | Leave empty for full list; or comma-separated symbols (e.g. RELIANCE,TCS,HDFCBANK) to reduce scope |
| **MNEMOS_BLACKLIST** | (none) | Comma-separated symbols to exclude from scanning |
| **FRICTION_ALERT_THRESHOLD** | 0.65 | Lower = more alerts; raise if too noisy |
| **CONFIDENCE_ALERT_THRESHOLD** | 0.60 | Same idea |
| **ALERT_COOLDOWN_SYMBOL_MINUTES** | 120 | Minutes before same symbol+signal can alert again |

---

## Colab 24/7 setup checklist

1. **Upload or clone** the MNEMOS project to Colab (e.g. zip → upload → unzip to `/content/mnemos2.0`).
2. **Open** `colab_setup.ipynb`.
3. **Cell 1**: Run to install dependencies.
4. **Cell 2**: Set the five required env vars (or use Colab Secrets). Set `MNEMOS_ROOT` if your project is not at `/content/mnemos2.0`.
5. **Cell 3**: Run to mount Google Drive (recommended for DB backups).
6. **Cell 4**: Run to start MNEMOS. This cell runs until you interrupt or the session disconnects.

After that, **no further input is needed**. The system will:

- Poll every 3 min (market hours) or 30 min (off hours).
- Store prices and signals in SQLite.
- Send alerts when friction + confidence exceed thresholds (and de-dup allows).
- Send a daily heartbeat to Telegram (once per day at the configured UTC hour).
- Generate weekly and monthly reports and send them to Telegram + email.
- Back up the DB to Drive periodically if Drive is mounted.

**When Colab disconnects**: Re-open the notebook and run **Cell 4** again to resume. There is no automatic reconnection on the free tier.

---

## Summary

**You must provide**: Telegram bot token, Telegram chat ID, Gmail address, Gmail app password, and alert email address.  
**You may optionally provide**: Custom watchlist, blacklist, or threshold/cooldown overrides.  
**Nothing else** is required for 24/7 operation on Colab.
