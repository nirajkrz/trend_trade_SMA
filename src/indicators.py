from __future__ import annotations
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=window).mean()


def roc(series: pd.Series, window: int) -> pd.Series:
    return series.pct_change(periods=window)


def slope(series: pd.Series, window: int = 5) -> pd.Series:
    """Simple slope proxy: difference over window."""
    return series.diff(window)
