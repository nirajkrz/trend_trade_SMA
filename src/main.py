from .data import load_history
from .strategy import generate_signals
from .backtest import run_backtest, run_eod_trader
import argparse


def main():
    parser = argparse.ArgumentParser(description="TQQQ/SQQQ strategies")
    parser.add_argument("--mode", choices=["baseline", "swing"], default="baseline", help="Which strategy to run")
    parser.add_argument("--initial-cash", type=float, default=10_000.0)
    # Swing-specific params
    parser.add_argument("--proximity", type=float, default=0.03, help="Proximity to SMA250 to avoid/exit (e.g., 0.03 for 3%)")
    parser.add_argument("--tp", type=float, default=0.10, help="Take profit threshold (e.g., 0.10 for +10%)")
    parser.add_argument("--sl", type=float, default=-0.05, help="Stop loss threshold (e.g., -0.05 for -5%)")
    parser.add_argument("--allow-short", action="store_true", help="Allow SQQQ long allocation when downtrend")
    parser.add_argument("--max-trades-per-day", type=int, default=2)
    parser.add_argument("--years", type=int, default=2, help="Window size to trade over (years)")
    parser.add_argument("--lookback-years", type=int, default=10, help="History to download for indicators (years)")
    parser.add_argument("--print-trades", action="store_true", help="Print trade list (swing mode)")
    parser.add_argument("--trades-limit", type=int, default=20, help="How many trades to print from the end")
    args = parser.parse_args()

    symbols = ["TQQQ", "SQQQ"]

    if args.mode == "baseline":
        df = load_history(symbols=symbols, period="max")
        signals = generate_signals(df)
        equity_curve, stats = run_backtest(price=df, signals=signals, initial_cash=args.initial_cash)

        print("Backtest complete (baseline).")
        print("Stats:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        return

    # swing mode
    period = f"{args.lookback_years}y"
    df = load_history(symbols=symbols, period=period)
    equity, stats, trades = run_eod_trader(
        close=df,
        proximity=args.proximity,
        tp=args.tp,
        sl=args.sl,
        allow_short=args.allow_short,
        max_trades_per_day=args.max_trades_per_day,
        initial_cash=args.initial_cash,
        window_years=args.years,
    )

    print("Backtest complete (swing).")
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    if args.print_trades:
        print("\nRecent trades:")
        for t in trades[-args.trades_limit:]:
            d = getattr(t["date"], "date", lambda: t["date"])()
            print(f"{d} {t['action']:16s} qty={t['qty']:.4f} px=${t['px']:.2f} cash=${t['cash']:.2f}")


if __name__ == "__main__":
    main()
