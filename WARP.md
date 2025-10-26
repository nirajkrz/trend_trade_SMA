# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

- Environment setup (recommended):
  - python -m venv .venv && source .venv/bin/activate
  - pip install -r requirements.txt
- Run the backtest:
  - python -m src.main
- Tests (pytest is not pinned in requirements):
  - pip install -U pytest
  - Run all tests: pytest -q
  - Run a single test: pytest tests/test_strategy.py::test_generate_signals_runs -q
  - Filter by keyword: pytest -k signals -q
- Linting/format: none configured in this repo.

## Architecture and data flow

High-level flow (single pipeline):
- src/data.py load_history: Downloads adjusted Close data for symbols (TQQQ, SQQQ) via yfinance and returns a Date-indexed DataFrame of Close prices.
- src/strategy.py generate_signals: Produces a daily allocation signal Series (+1 TQQQ, -1 SQQQ, 0 cash) using:
  - Indicators from src/indicators.py (sma, roc, slope)
  - Trend bias: TQQQ Close above SMA250 → +1; weakened to 0 if SMA50 slope < 0 and distance to SMA250 is shrinking
  - Mean reversion override: ROC(10) < -0.07 → +1; ROC(10) > +0.07 → -1
  - MR overrides trend when non-zero
- src/backtest.py run_backtest: Maps signals to daily returns and builds equity curve with stats:
  - Portfolio return = TQQQ return when signal > 0; SQQQ return when signal < 0; 0 when cash
  - Returns simple close-to-close; no fees/slippage
  - Stats include final_equity, CAGR (from first/last dates), and max_drawdown (min of equity/peak - 1)
- src/main.py: Orchestrates the pipeline: load_history → generate_signals → run_backtest → print stats.

## Usage notes specific to this repo

- Package layout: This is a src-style package without __init__.py (namespace package). Use python -m src.main from repo root; running python src/main.py will fail due to relative imports.
- Data dependency: Tests and runs fetch live data from Yahoo via yfinance; network access is required and initial calls may be slow or rate-limited.
- Tests: The single test (tests/test_strategy.py) is a smoke test over a 1y period and asserts index alignment of signals with downloaded data.
- No lint/type tooling or CI config is present.
