# MNEMOS 2.1

**Institutional-grade, self-healing market intelligence for Indian equity markets.**  
Runs on free infrastructure (Google Colab); 150+ NSE stocks by market cap, confidence-based alerts, performance attribution, and reporting.

## What it does

- **Monitors** 150+ NSE stocks (default watchlist by market cap); 3 min during market hours.
- **Detects friction**: panic selling, silent accumulation, sector lag, news underreaction/overreaction.
- **Confidence engine**: Only alerts when friction + confidence exceed thresholds; uses liquidity, volatility, data quality, historical win rate.
- **De-duplication**: Cooldown per symbol + signal type; severity escalation.
- **Performance attribution**: +1D, +3D, +5D outcomes in SQLite; win rate, avg return, drawdown.
- **Risk governance**: Blacklist, volatility cap, liquidity filter.
- **Watchdog + supervisor**: Auto-restart with memory/restart guardrails; daily heartbeat to Telegram.
- **Reports**: Weekly intelligence and monthly performance (Telegram + email, Markdown).
- **Backtesting**: Replay signals, evaluate rules, CSV + report.

## Quick start (Google Colab)

1. Upload the project to Colab (zip to `/content` and unzip, or clone).
2. Open `colab_setup.ipynb` and run cells in order.
3. Set **TELEGRAM_BOT_TOKEN**, **TELEGRAM_CHAT_ID**, **GMAIL_USER**, **GMAIL_APP_PASSWORD**, **ALERT_EMAIL_TO** in the env cell (or Colab Secrets).
4. Run the last cell to start MNEMOS 24/7. Heartbeats in notebook; alerts and daily heartbeat to Telegram/Email.

## Where your input is needed

| Input | Where | Required |
|-------|--------|----------|
| **Telegram bot token** | Colab env or `.env` → `TELEGRAM_BOT_TOKEN` | For Telegram alerts + daily heartbeat |
| **Telegram chat ID** | Colab env or `.env` → `TELEGRAM_CHAT_ID` | For Telegram |
| **Gmail address** | `.env` / Colab → `GMAIL_USER`, `ALERT_EMAIL_TO` | For email alerts + reports |
| **Gmail app password** | `.env` / Colab → `GMAIL_APP_PASSWORD` | Not account password |
| **Watchlist** | `.env` → `MNEMOS_WATCHLIST` or empty for 150+ default | Optional |
| **Blacklist** | `.env` → `MNEMOS_BLACKLIST` | Optional |

Everything else has defaults (see `.env.example`).

## Project layout

```
mnemos2.0/
  core/           # Data fetcher, news engine, feature engineering
  engine/         # Friction, confidence, scheduler, backtest, orchestrator
  alerts/         # Telegram + Email + dedup
  storage/        # SQLite (schema v2) + backups
  config/         # Settings from .env
  health/         # Watchdog, supervisor, daily heartbeat
  analytics/      # Performance attribution
  risk/            # Governance (blacklist, volatility, liquidity)
  optimizer/      # Strategy versions, threshold suggestions
  reports/        # Weekly/monthly report generator
  scripts/        # performance_dashboard.py
  tests/
  main.py
  colab_setup.ipynb
  docs/
```

## Local run

```bash
cp .env.example .env
# Edit .env: Telegram, Gmail, optional watchlist/blacklist
pip install -r requirements.txt
python main.py                  # forever with supervisor
python main.py --no-supervisor # forever without supervisor
python main.py --once           # single tick
python main.py --test           # 2 symbols, one tick
python scripts/performance_dashboard.py   # attribution + recent signals
```

## Inputs required from you

See **[INPUTS_REQUIRED.md](docs/INPUTS_REQUIRED.md)** for the exact list: Telegram + Gmail credentials for alerts and daily heartbeat; optional watchlist/blacklist. After setting those on Colab, the system runs 24/7 with no further input.

## Docs

- [Installation](docs/INSTALLATION.md)
- [Deployment (Colab)](docs/DEPLOYMENT.md)
- [Maintenance](docs/MAINTENANCE.md)
- [Operations](docs/OPERATIONS.md)
- [Strategy guide](docs/STRATEGY_GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Scaling](docs/SCALING.md)

## Requirements

- Python 3.8+
- Free tier: Colab, yfinance, Google News RSS, Telegram Bot API, Gmail SMTP. No paid APIs.

Not financial advice.
