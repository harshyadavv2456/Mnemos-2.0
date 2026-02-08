# MNEMOS 2.1 – Operations Manual

## Daily operations

### Heartbeat
- **Daily heartbeat** is sent to Telegram once per day (UTC hour configurable via `DAILY_HEARTBEAT_HOUR_UTC`). It summarizes last 24h heartbeats and restart count.
- **Per-tick heartbeats** are written to the DB and logs; use them to confirm the process is running.

### Restarts
- **Supervisor** (default when running `python main.py`) restarts the main loop on uncaught exception, after `SUPERVISOR_RESTART_DELAY_SEC`, subject to **watchdog guardrails**:
  - Memory must be below `WATCHDOG_MAX_MEMORY_MB`.
  - Restarts in the last hour must be below `WATCHDOG_MAX_RESTARTS_PER_HOUR`.
- Restart events are logged in the `restarts` table.

### Backups
- **Local**: `data/backups/mnemos_*.db` every `backup_interval_ticks` (default 20).
- **Drive**: If Drive is mounted and `set_drive_mount()` was called, the same backup is copied to Google Drive under `mnemos_backups/`.

### Reports
- **Weekly report**: Markdown summary of signal activity and system health; sent to Telegram and email (day set by `WEEKLY_REPORT_DAY`, 0=Monday).
- **Monthly report**: Performance attribution (win rate, avg return, drawdown) plus activity; sent to Telegram and email (day set by `MONTHLY_REPORT_DAY`).

## Monitoring

- **Logs**: `logs/mnemos.log`. Rotate or truncate externally if needed.
- **DB**: `data/mnemos.db`. Use `scripts/performance_dashboard.py` for a quick view of attribution and recent signals/heartbeats.
- **Telegram**: Alerts and daily heartbeat; ensure token and chat ID are set.

## Shutdown and restart

- **Graceful**: Interrupt the process (Ctrl+C or Colab “Interrupt execution”). No special shutdown hook; in-flight tick may complete.
- **Restart**: Run `python main.py` again (or re-run the Colab “Run MNEMOS 24/7” cell). Schema and migrations run on startup.

## Colab-specific

- **Session expiry**: Free Colab sessions can disconnect. Re-open the notebook and run the “Run MNEMOS 24/7” cell to resume. No automatic reconnection.
- **Keepalive**: Keep the tab active or run a JavaScript cell periodically to try to preserve the session (see notebook).
- **Drive**: Mount Drive so backups and (if you copy them) DB/reports persist across sessions.
