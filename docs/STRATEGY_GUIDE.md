# MNEMOS 2.1 – Strategy Guide

## Signal types (friction)

The system detects five friction patterns:

1. **Panic selling**: Large negative return + elevated volume.
2. **Silent accumulation**: Small positive return + below-average volume.
3. **Sector lag**: Stock underperforming peers (sector-relative strength).
4. **News underreaction**: Headlines present but price move small.
5. **Overreaction**: Large single-day move (up or down).

Each pattern contributes to a **friction score** (0–1). Alerts are sent only when:
- Friction score ≥ `FRICTION_ALERT_THRESHOLD` (default 0.65), and
- **Confidence** ≥ `CONFIDENCE_ALERT_THRESHOLD` (default 0.60).

## Confidence

Confidence is a composite of:
- Friction score
- Liquidity (volume ratio)
- Volatility (inverse: lower vol → higher score)
- Data quality (completeness of features)
- Historical win rate (from outcomes, when enough samples exist)

Only alerts above the confidence threshold are sent. Confidence history is stored in `confidence_history`.

## De-duplication

- **Cooldown**: Same symbol + same signal type cannot trigger an alert again within `ALERT_COOLDOWN_SYMBOL_MINUTES` (default 120).
- **Rate limits**: Telegram and email have global and per-symbol rate limits (see `.env.example`).

## Risk governance

Before scoring, symbols are filtered by:
- **Blacklist**: `MNEMOS_BLACKLIST` (comma-separated) excludes symbols.
- **Volatility**: Symbols with volatility above `MAX_VOLATILITY_PCT` are skipped.
- **Liquidity**: Handled via feature availability; low-liquidity names may have no or weak features.

## Performance attribution

- For each stored signal we compute **+1D, +3D, +5D** returns (when price data exists).
- **Win rate**, **avg return**, **drawdown** are available via the analytics module and the performance dashboard (`scripts/performance_dashboard.py`).

## Strategy optimizer

- **Suggest thresholds**: `optimizer.strategy_optimizer.suggest_thresholds()` uses recent win rate to suggest friction/confidence thresholds.
- **Rank rules**: `rank_rules_by_performance()` returns signal types ordered by historical win rate.
- **Strategy versions**: Configs can be saved and versioned in `strategy_versions` for reproducibility.

## Backtesting

- **Run backtest**: `engine.backtest.run_and_export_backtest(since_dt)` replays signals since a date, joins outcomes, and writes CSV + Markdown report to `reports/`.
- Use backtest reports to compare rule effectiveness and adjust thresholds.
