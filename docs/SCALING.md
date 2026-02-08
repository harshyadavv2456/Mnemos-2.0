# MNEMOS 2.1 – Scaling Roadmap

Current design targets **free tier** and **Indian NSE only**, with a watchlist of ~40 symbols and 3-min polling during market hours.

## Current limits (by design)

- **Symbols**: Default watchlist ~40; configurable via `MNEMOS_WATCHLIST`. yfinance can handle more, but Colab and rate limits (Telegram, Gmail) become the bottleneck.
- **Polling**: 3 min during market hours, 30 min off. Reducing below 2 min increases Yahoo request rate and Colab CPU usage.
- **News**: One RSS fetch per symbol per tick for friction; Google News RSS has no documented hard limit but heavy use can get throttled.
- **Alerts**: 60 s between Telegram messages, 3 per symbol per hour; 5 min between emails. Increasing symbol count increases alert volume; consider raising thresholds or tightening rate limits.

## Scaling options (when you outgrow free tier)

### 1. More symbols (same Colab)

- Add symbols to `MNEMOS_WATCHLIST` (comma-separated, NSE only `.NS`). Start with 50–80; monitor Colab memory and runtime stability.
- If you hit memory or timeout: split watchlist into two Colab notebooks (e.g. by sector), each running its own MNEMOS instance with different env watchlists.

### 2. Faster polling

- Change `POLL_INTERVAL_MARKET_MIN` to 2 in `.env`. Risk: more yfinance calls, possible rate limiting or Colab throttling.
- Keep 5-min **intraday** bars from yfinance; do not go below 5m interval for free tier (1m often requires paid/subscription data).

### 3. Multiple Colab runtimes

- Run two (or more) notebooks with different `MNEMOS_WATCHLIST` and same Telegram/Gmail. Each instance runs independently; alert rate limits are shared (Telegram/email), so you may need to increase intervals or reduce symbols per instance.

### 4. Move off Colab (e.g. free-tier VM)

- Run `main.py` on a free-tier cloud VM (e.g. Oracle Cloud Free, AWS free tier, GCP free tier). Same code; no Colab timeout. Use cron or systemd to auto-restart on reboot.
- Optionally add a small PostgreSQL or MySQL for central storage and run multiple workers against the same DB (would require code changes to use a shared DB instead of local SQLite).

### 5. Paid data and infra (beyond free tier)

- **Data**: Replace yfinance with a paid Indian market data provider (NSE/BSE official or licensed) for more symbols, lower latency, and 1m bars if needed.
- **Compute**: Run on a paid Colab plan or a VPS for 24/7 uptime and no session limits.
- **Alerts**: Add more channels (Slack, webhooks) and/or a queue (Redis, SQS) to decouple scoring from delivery and respect rate limits.

### 6. Indian markets only

- MNEMOS 2.0 is built for **NSE (.NS)**. For BSE use `.BO` in symbols and ensure yfinance supports the tickers. All logic (sector relative, news search) remains India-focused; no code change needed for “Indian only” beyond symbol list and optional BSE addition.

## Summary

- **Today**: 40 symbols, 3-min polling, one Colab session, Telegram + Gmail. Suitable for 5+ years of personal use with minor maintenance (logs, backups, env).
- **Next**: Add symbols (50–80), or split into 2 Colab instances by watchlist.
- **Later**: Migrate to a free VM for 24/7; optionally move to paid data and shared DB for multi-symbol scaling.
