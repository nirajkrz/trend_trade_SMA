# TQQQ/SQQQ Trend + Mean Reversion Backtester

A Python tool to backtest a combined trend-following and mean-reversion strategy using 50/250-day moving averages and rate-of-change (ROC) on TQQQ/SQQQ, starting with $10,000.

## Key ideas
- Trend: stay long TQQQ while Close > 250-day SMA; exit when trend weakens toward the 250-day SMA.
- Mean reversion: use ROC extremes to enter contrarian trades and exit on snap-back.
- Universe: TQQQ and SQQQ only.

## Quick start
1. Create a virtualenv (optional) and install requirements:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run a sample backtest:
   ```bash
   python -m src.main
   ```

## Notes
- Data source: yfinance (Yahoo! Finance). Symbols: `TQQQ`, `SQQQ`.
- Initial capital: $10,000. No fees/slippage by default.
- This repository is a starting point—tune rules and parameters as desired.
