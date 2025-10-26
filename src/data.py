from __future__ import annotations
import pandas as pd
import yfinance as yf


def load_history(symbols: list[str], period: str = "max", interval: str = "1d") -> pd.DataFrame:
    """
    Download OHLCV for given symbols and return a single price frame of the 'Close' column
    normalized to a common Date index.
    """
    data = {}
    for s in symbols:
        hist = yf.download(s, period=period, interval=interval, auto_adjust=True, progress=False)
        hist = hist.rename(columns=lambda c: c.strip())
        sr = hist["Close"].copy()
        sr.name = s
        data[s] = sr
    close = pd.concat(data.values(), axis=1)
    close.index.name = "Date"
    close = close.dropna(how="all")
    return close
