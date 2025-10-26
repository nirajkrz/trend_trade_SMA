from __future__ import annotations
import pandas as pd
from .indicators import sma


def run_backtest(price: pd.DataFrame, signals: pd.Series, initial_cash: float = 10_000.0):
    """
    Backtest a daily signal on a two-asset universe (TQQQ, SQQQ):
    - signal +1 => long TQQQ
    - signal -1 => long SQQQ
    - signal 0  => cash
    Assumes daily close-to-close rebalancing, no fees.
    """
    prices = price[["TQQQ", "SQQQ"]].dropna(how="all").copy()
    signals = signals.reindex(prices.index).fillna(0.0)

    # Daily simple returns
    rets = prices.pct_change().fillna(0.0)

    # Portfolio daily return
    port_ret = (
        rets["TQQQ"] * (signals.clip(lower=0))  # +1 alloc maps to TQQQ
        + rets["SQQQ"] * (signals.clip(upper=0).abs())  # -1 alloc maps to SQQQ
    )

    equity = (1 + port_ret).cumprod() * initial_cash

    stats = {
        "final_equity": float(equity.iloc[-1]) if len(equity) else initial_cash,
        "cagr": _cagr(equity),
        "max_drawdown": _max_drawdown(equity),
    }
    return equity, stats


def regime_signal_tqqq(tqqq: pd.Series, proximity: float = 0.03) -> pd.Series:
    """Compute SMA50/SMA250 regime signal on TQQQ with proximity filter.
    Returns +1 (uptrend), -1 (downtrend), 0 (cash/avoid)."""
    s50 = sma(tqqq, 50)
    s250 = sma(tqqq, 250)
    dist = (tqqq - s250) / s250
    near_ma = dist.abs() <= proximity
    shrinking = dist.abs() < dist.abs().shift(5)
    up = (tqqq > s250) & (s50 >= s250) & ~(near_ma & shrinking)
    down = (tqqq < s250) & (s50 <= s250) & ~(near_ma & shrinking)
    sig = pd.Series(0, index=tqqq.index, dtype=int)
    sig[up] = 1
    sig[down] = -1
    return sig


def run_eod_trader(
    close: pd.DataFrame,
    proximity: float = 0.03,
    tp: float = 0.10,
    sl: float = -0.05,
    allow_short: bool = False,
    max_trades_per_day: int = 2,
    initial_cash: float = 10_000.0,
    window_years: int = 2,
):
    """
    End-of-day trading simulator on TQQQ (optionally SQQQ) using regime + TP/SL.
    - Regime uses SMA50/SMA250 with 5-day shrinking proximity filter.
    - Entries/exits at the close, max `max_trades_per_day` events per day.
    - Default is long/cash on TQQQ only (allow_short=False).
    Returns (equity_curve, stats, trades), where trades is a list of dicts.
    """
    prices = close[["TQQQ", "SQQQ"]].dropna(how="all").copy()
    # Regime over full history, trade over last `window_years`
    sig_full = regime_signal_tqqq(prices["TQQQ"], proximity=proximity)

    end = prices.index[-1]
    start = prices.index[prices.index.get_indexer([end - pd.DateOffset(years=window_years)], method="backfill")][0]
    idx = prices.loc[start:end].index

    cash = float(initial_cash)
    pos_t = 0.0
    pos_s = 0.0
    entry_price = None
    entry_symbol: str | None = None
    trades: list[dict] = []

    equity = pd.Series(index=idx, dtype=float)

    for dt in idx:
        px_t = float(prices.loc[dt, "TQQQ"]) if not pd.isna(prices.loc[dt, "TQQQ"]) else 0.0
        px_s = float(prices.loc[dt, "SQQQ"]) if not pd.isna(prices.loc[dt, "SQQQ"]) else 0.0
        desired = int(sig_full.loc[dt]) if dt in sig_full.index else 0
        trades_today = 0

        def open_pnl() -> float:
            if entry_price is None:
                return 0.0
            if entry_symbol == "TQQQ" and pos_t > 0:
                return (px_t / entry_price) - 1.0
            if entry_symbol == "SQQQ" and pos_s > 0:
                return (px_s / entry_price) - 1.0
            return 0.0

        # Exits first
        if entry_symbol == "TQQQ" and pos_t > 0:
            pnl = open_pnl()
            if pnl >= tp and trades_today < max_trades_per_day:
                cash += pos_t * px_t
                trades.append({"date": dt, "action": "SELL TQQQ (TP)", "qty": pos_t, "px": px_t, "cash": cash})
                pos_t = 0.0; entry_symbol = None; entry_price = None; trades_today += 1
            elif pnl <= sl and trades_today < max_trades_per_day:
                cash += pos_t * px_t
                trades.append({"date": dt, "action": "SELL TQQQ (SL)", "qty": pos_t, "px": px_t, "cash": cash})
                pos_t = 0.0; entry_symbol = None; entry_price = None; trades_today += 1
            elif desired != 1 and trades_today < max_trades_per_day:
                cash += pos_t * px_t
                trades.append({"date": dt, "action": "SELL TQQQ (Regime)", "qty": pos_t, "px": px_t, "cash": cash})
                pos_t = 0.0; entry_symbol = None; entry_price = None; trades_today += 1
        elif allow_short and entry_symbol == "SQQQ" and pos_s > 0:
            pnl = open_pnl()
            if pnl >= tp and trades_today < max_trades_per_day:
                cash += pos_s * px_s
                trades.append({"date": dt, "action": "SELL SQQQ (TP)", "qty": pos_s, "px": px_s, "cash": cash})
                pos_s = 0.0; entry_symbol = None; entry_price = None; trades_today += 1
            elif pnl <= sl and trades_today < max_trades_per_day:
                cash += pos_s * px_s
                trades.append({"date": dt, "action": "SELL SQQQ (SL)", "qty": pos_s, "px": px_s, "cash": cash})
                pos_s = 0.0; entry_symbol = None; entry_price = None; trades_today += 1
            elif desired != -1 and trades_today < max_trades_per_day:
                cash += pos_s * px_s
                trades.append({"date": dt, "action": "SELL SQQQ (Regime)", "qty": pos_s, "px": px_s, "cash": cash})
                pos_s = 0.0; entry_symbol = None; entry_price = None; trades_today += 1

        # Entries after exits
        if trades_today < max_trades_per_day and cash > 0:
            if desired == 1:
                qty = cash / px_t if px_t > 0 else 0.0
                if qty > 0:
                    pos_t = qty; cash = 0.0; entry_symbol = "TQQQ"; entry_price = px_t
                    trades.append({"date": dt, "action": "BUY TQQQ", "qty": qty, "px": px_t, "cash": cash}); trades_today += 1
            elif allow_short and desired == -1:
                qty = cash / px_s if px_s > 0 else 0.0
                if qty > 0:
                    pos_s = qty; cash = 0.0; entry_symbol = "SQQQ"; entry_price = px_s
                    trades.append({"date": dt, "action": "BUY SQQQ", "qty": qty, "px": px_s, "cash": cash}); trades_today += 1

        # Mark equity
        equity.loc[dt] = cash + pos_t * (px_t if px_t else 0.0) + pos_s * (px_s if px_s else 0.0)

    stats = {
        "final_equity": float(equity.iloc[-1]) if len(equity) else initial_cash,
        "cagr": _cagr(equity),
        "max_drawdown": _max_drawdown(equity),
        "trades": len(trades),
    }
    return equity, stats, trades


def _cagr(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    days = (equity.index[-1] - equity.index[0]).days
    if days <= 0:
        return 0.0
    years = days / 365.25
    return float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1)


def _max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    peak = equity.cummax()
    dd = (equity / peak - 1.0).min()
    return float(dd)
