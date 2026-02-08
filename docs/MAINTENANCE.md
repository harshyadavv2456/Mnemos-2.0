# MNEMOS 2.1 – Maintenance Guide

## Logs

- **Location**: `logs/mnemos.log` (overwritten each run unless you rotate).
- **Heartbeats**: Also in DB table `heartbeats` (ts, status, message). Use for crash detection and uptime checks.

## Database

- **Path**: `data/mnemos.db` (SQLite).
- **Tables**:
  - `prices`: OHLCV bars.
  - `signals`: Friction signals (symbol, score, explanation, signal_type, confidence, severity).
  - `outcomes`: Performance attribution (signal_id, return_1d, return_3d, return_5d).
  - `confidence_history`: Confidence over time.
  - `alert_lock`: De-dup cooldown (symbol, signal_type, last_alert_ts).
  - `restarts`: Watchdog restart log.
  - `summaries`, `heartbeats`, `strategy_versions`, `backtest_runs`, `report_jobs`.

### Backup

- **Local**: Backups go to `data/backups/` as `mnemos_YYYYMMDD_HHMMSS.db` (every N ticks when running forever).
- **Drive**: If Drive is mounted and `set_drive_mount()` is called, backups also go to `mnemos_backups/` on Google Drive.
- **Manual**: Copy `data/mnemos.db` or run `storage.backup.backup_to_local()`.

### Cleanup

- To avoid unbounded growth, you can periodically delete old `prices` or `heartbeats` (e.g. keep last 30 days). Example (run with care):

  ```sql
  DELETE FROM heartbeats WHERE ts < datetime('now', '-30 days');
  DELETE FROM prices WHERE dt < datetime('now', '-90 days');
  ```

- Or archive old backups and remove files under `data/backups/` and in Drive.

## Configuration

- All config is in **`.env`** (or Colab env). See `.env.example`.
- After changing `.env`, restart the process (or re-run the Colab cell).

## Alerts not firing

- **Telegram**: Check token and chat ID; ensure rate limits (e.g. 60 s between messages, 3 per symbol per hour) aren’t blocking. Test with a single high-friction event or lower `FRICTION_ALERT_THRESHOLD`.
- **Email**: Use an **app password**, not account password. Check `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL_TO`. Rate limit: one email per `EMAIL_MIN_INTERVAL_SEC` (default 300).

## Data not updating

- **Market hours**: Polling is every 3 min during NSE hours (9:15–15:30 IST), 30 min outside. Check `engine.scheduler.is_market_hours()` and your machine’s timezone.
- **yfinance**: If Yahoo returns no data for a symbol, that symbol is skipped. Check symbols use `.NS` for NSE. Logs show “Fetch failed for SYMBOL”.

## Crashes and recovery

- **Heartbeats**: If heartbeats stop, the process likely crashed. Last row in `heartbeats` shows last status/message.
- **Restart**: On Colab, re-run the “Run MNEMOS forever” cell (or Run all). Locally, restart `python main.py`.
- **Auto-restart**: Colab does not restart automatically. For unattended long runs, consider a cron job or external scheduler that re-opens/reruns the notebook, or run MNEMOS on a small always-on host.

## Updates

- Pull or copy the latest code. Re-run `pip install -r requirements.txt` if `requirements.txt` changed. Restart the app.

## Security

- Never commit `.env` or paste tokens into public repos.
- Use Colab Secrets for tokens when possible. Rotate Telegram bot token or Gmail app password if exposed.
