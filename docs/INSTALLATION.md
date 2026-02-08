# MNEMOS 2.1 – Installation Guide

## Prerequisites

- **Python 3.8+** (Colab provides 3.10)
- **Network** for yfinance, Google News RSS, Telegram API, Gmail SMTP

## Local installation

### 1. Clone or copy project

```bash
cd /path/to/workspace
# If from git:
# git clone <your-repo-url> mnemos2.0
# cd mnemos2.0
```

### 2. Virtual environment (recommended)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration

```bash
cp .env.example .env
```

Edit `.env`:

- **Telegram**: Get bot token from [@BotFather](https://t.me/BotFather), chat ID from [@userinfobot](https://t.me/userinfobot). Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
- **Gmail**: Use [App Password](https://support.google.com/accounts/answer/185833) (not your account password). Set `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL_TO`.
- **Watchlist** (optional): Comma-separated NSE symbols, e.g. `MNEMOS_WATCHLIST=RELIANCE,TCS,HDFCBANK`. Leave empty to use built-in list of 40 liquid Indian stocks.

### 5. Run

```bash
python main.py           # adaptive loop (market hours: 3 min, off: 30 min)
python main.py --once    # single cycle then exit
python main.py --test    # test with 2 symbols, one tick
```

## Google Colab

See [Deployment guide](DEPLOYMENT.md). Use `colab_setup.ipynb`: install deps, set env, mount Drive (optional), run the “Run MNEMOS forever” cell.

## Verifying installation

After `python main.py --test` you should see:

- Log lines in console and in `logs/mnemos.log`
- `data/mnemos.db` created with tables `prices`, `signals`, `summaries`, `heartbeats`
- No unhandled exceptions

If Telegram/Gmail are set, trigger a high friction event (or lower `FRICTION_ALERT_THRESHOLD` in `.env`) to confirm alerts.
