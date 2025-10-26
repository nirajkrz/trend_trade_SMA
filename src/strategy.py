from __future__ import annotations
import pandas as pd
from .indicators import sma


def generate_signals(prices: pd.DataFrame, proximity: float = 0.07) -> pd.Series:
    """
    Daily end-of-day signals using SMA50/SMA250 on TQQQ.

    Semantics (long/cash):
    - BUY/HOLD (+1): when Close > SMA250 and SMA50 >= SMA250 (uptrend confirmation)
    - EXIT/CASH (0): when trend weakens as price moves toward SMA250, defined as
        distance = (Close - SMA250)/SMA250 ≤ proximity (default 7%) AND
        distance is shrinking vs 5 trading days ago.
    - Otherwise stay in CASH (0).

    Notes:
    - Signals are evaluated on daily Close (EOD decision) and applied next close-to-close in the backtest.
    - This implementation is long/cash only (no short allocation to SQQQ).
    """
    close = prices[["TQQQ", "SQQQ"]].copy()
    tqqq = close["TQQQ"].dropna()

    s50 = sma(tqqq, 50)
    s250 = sma(tqqq, 250)
    dist = (tqqq - s250) / s250

    signal = pd.Series(0.0, index=tqqq.index)

    # Uptrend confirmation
    uptrend = (tqqq > s250) & (s50 >= s250)
    signal[uptrend] = 1.0

    # Exit condition: approaching SMA250 within proximity and distance shrinking vs 5 days ago
    weaken = uptrend & (dist <= proximity) & (dist < dist.shift(5))
    signal[weaken] = 0.0

    return signal.fillna(0.0)
