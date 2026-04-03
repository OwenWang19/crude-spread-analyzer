"""
main.py
-------
End-to-end pipeline: fetch → analyse → signal → visualise → report

Usage:
    python main.py                     # full run, last 5 years
    python main.py --start 2022-01-01  # custom start date
    python main.py --no-plots          # analysis only, skip HTML exports
"""

import argparse
import sys
from datetime import date

from src.data_fetcher    import fetch_prices
from src.spread_analyzer import (compute_spreads, add_zscore_signals,
                                  cointegration_test, run_all_stationarity_tests,
                                  summary_stats, rolling_crack_vs_crude)
from src.signals         import run_signal_report
from src.visualizer      import (plot_crude_prices, plot_wti_brent_spread,
                                  plot_crack_spread, plot_product_cracks,
                                  plot_rolling_correlation, plot_pnl_comparison,
                                  save_all)


def print_header(title: str) -> None:
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")


def main(start: str = "2019-01-01", save_plots: bool = True) -> None:

    # ── 1. Fetch Data ──────────────────────────────────────────────────────────
    print_header("1 / 5  Fetching Energy Futures Data")
    df = fetch_prices(start=start)
    print(f"  Loaded {len(df)} daily observations")
    print(f"  Date range: {df.index[0].date()} → {df.index[-1].date()}")
    print(f"\n  Latest prices ($/bbl):")
    print(df.tail(3).round(2).to_string())

    # ── 2. Compute Spreads ─────────────────────────────────────────────────────
    print_header("2 / 5  Computing Spreads & Z-Scores")
    spreads = add_zscore_signals(compute_spreads(df))

    print("\n  Spread Summary Statistics:")
    print(summary_stats(spreads).to_string())

    # ── 3. Statistical Tests ───────────────────────────────────────────────────
    print_header("3 / 5  Statistical Tests")

    coint_res = cointegration_test(df)
    print(f"\n  Cointegration Test:")
    for k, v in coint_res.items():
        print(f"    {k:<28}: {v}")

    print(f"\n  ADF Stationarity Tests:")
    print(run_all_stationarity_tests(spreads).to_string())

    corr = rolling_crack_vs_crude(df, spreads)
    print(f"\n  Rolling WTI vs Crack Correlation (latest): {corr.dropna().iloc[-1]:.4f}")

    # ── 4. Signal Generation & Backtest ───────────────────────────────────────
    print_header("4 / 5  Mean-Reversion Signal Backtest")
    signal_report = run_signal_report(spreads)
    for name, (bt, metrics) in signal_report.items():
        print(f"\n  [{name}]")
        for k, v in metrics.items():
            print(f"    {k:<28}: {v}")

    # ── 5. Visualisation ───────────────────────────────────────────────────────
    if save_plots:
        print_header("5 / 5  Generating Interactive Charts → reports/")
        bt_wb    = signal_report["WTI_Brent_Spread"][0]
        bt_crack = signal_report["Crack_321"][0]

        figs = {
            "01_crude_prices":        plot_crude_prices(df),
            "02_wti_brent_spread":    plot_wti_brent_spread(spreads, bt_wb),
            "03_crack_spread":        plot_crack_spread(spreads, bt_crack),
            "04_product_cracks":      plot_product_cracks(spreads),
            "05_rolling_correlation": plot_rolling_correlation(corr),
            "06_pnl_comparison":      plot_pnl_comparison(bt_wb, bt_crack),
        }
        save_all(figs, output_dir="reports")
        print("\n  ✓ All charts saved. Open reports/*.html in your browser.")
    else:
        print("\n  [Plots skipped — run without --no-plots to generate HTML charts]")

    print_header("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crude Spread Analyser")
    parser.add_argument("--start",    default="2019-01-01",
                        help="Start date for data fetch (YYYY-MM-DD)")
    parser.add_argument("--no-plots", action="store_true",
                        help="Skip plot generation")
    args = parser.parse_args()
    main(start=args.start, save_plots=not args.no_plots)
