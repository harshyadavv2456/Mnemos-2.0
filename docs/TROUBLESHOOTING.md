# MNEMOS 2.1 – Troubleshooting

## No alerts

- **Confidence**: Alerts require both friction and confidence above threshold. Check `CONFIDENCE_ALERT_THRESHOLD` and `FRICTION_ALERT_THRESHOLD`. Lower them temporarily to test.
- **De-dup**: Same symbol + signal type may be in cooldown. Check `alert_lock` table or wait `ALERT_COOLDOWN_SYMBOL_MINUTES`.
- **Telegram/Email**: Verify `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `ALERT_EMAIL_TO`. Use Gmail **App Password**, not account password.
- **Risk**: Symbol might be blacklisted or filtered by volatility. Check `MNEMOS_BLACKLIST` and `MAX_VOLATILITY_PCT`.

## No data / empty features

- **Market hours**: During off-hours, yfinance may return little or no intraday data. Daily data should still be available.
- **Symbols**: Ensure NSE symbols use `.NS` suffix. Watchlist is auto-normalized.
- **yfinance errors**: Check logs for "Fetch failed for SYMBOL". Some symbols may be delisted or renamed.

## High memory / restarts

- **Watchdog**: If memory exceeds `WATCHDOG_MAX_MEMORY_MB`, the supervisor may refuse to restart. Increase the limit or reduce the watchlist size.
- **Restart loop**: If restarts exceed `WATCHDOG_MAX_RESTARTS_PER_HOUR`, the process exits. Check logs for the underlying exception; fix config or code and run again.

## Daily heartbeat not received

- **Hour**: Daily heartbeat is sent only at `DAILY_HEARTBEAT_HOUR_UTC` (default 4). Ensure the process is running at that time.
- **Telegram**: Same token/chat ID as for alerts. Test with a manual alert.

## Reports not sent

- **Weekly**: Runs when `datetime.utcnow().weekday() == WEEKLY_REPORT_DAY` and hour is 4. Default day 0 = Monday.
- **Monthly**: Runs when `datetime.utcnow().day == MONTHLY_REPORT_DAY` and hour is 4.
- **Delivery**: Uses same Telegram/email as alerts. Check logs for "Weekly report" / "Monthly report failed".

## Outcomes empty

- Outcomes are filled when we have **future** prices (1d, 3d, 5d after signal). Run the process for several days so that past signals have forward data.
- **Outcome backfill** runs periodically in the main loop; it links signals to prices and computes returns. Ensure `prices` has data for the symbol and dates.

## Colab disconnects

- Free Colab has idle limits. Keep the tab active or use a keepalive (see notebook).
- After disconnect, re-run the notebook from the “Run MNEMOS 24/7” cell. Mount Drive so backups and DB are not lost.

## DB locked / SQLite errors

- Only one process should write to the DB. If running multiple notebooks or scripts, use a single main process.
- For "database is locked", ensure no other tool (e.g. DB browser) has the file open for writing.
