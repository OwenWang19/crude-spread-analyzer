"""
signals.py
----------
Mean-reversion arbitrage signal generation based on z-score thresholds.

Signal logic (standard for stat-arb / spread trading desks):
  - Z-score > +entry_z  → spread is stretched HIGH  → SHORT the spread
                           (e.g., WTI premium too wide → short WTI, long Brent)
  - Z-score < -entry_z  → spread is compressed LOW   → LONG the spread
  - |Z-score| < exit_z  → spread has normalised      → EXIT / close position

Backtesting framework:
  - Daily rebalancing
  - No transaction costs (can be added)
  - Position sizing: ±1 unit per signal (equal-weight)
  - P&L = daily change in spread × position
"""

import numpy as np
import pandas as pd


# ── Signal Generation ─────────────────────────────────────────────────────────

def generate_signals(zscore: pd.Series,
                     entry_z: float = 1.5,
                     exit_z: float  = 0.5) -> pd.Series:
    """
    Returns a position series: +1 (long spread), -1 (short spread), 0 (flat).
    Uses a stateful loop to avoid look-ahead bias.
    """
    position = pd.Series(0.0, index=zscore.index, name="Position")
    pos = 0

    for i, (date, z) in enumerate(zscore.items()):
        if np.isnan(z):
            continue
        if pos == 0:
            if z > entry_z:
                pos = -1   # short: spread too wide
            elif z < -entry_z:
                pos = 1    # long: spread too tight
        elif pos == 1 and z >= -exit_z:
            pos = 0        # mean-reversion: exit long
        elif pos == -1 and z <= exit_z:
            pos = 0        # mean-reversion: exit short
        position.iloc[i] = pos

    return position


# ── Backtest Engine ───────────────────────────────────────────────────────────

def backtest(spread: pd.Series,
             position: pd.Series,
             initial_capital: float = 100_000) -> pd.DataFrame:
    """
    Vectorised P&L calculation.
    P&L per day = position[t-1] × (spread[t] - spread[t-1])
    Assumes 1 contract = 1 barrel equivalent (scaled by initial_capital).
    """
    spread_chg = spread.diff()
    daily_pnl  = position.shift(1) * spread_chg * (initial_capital / spread.mean())

    result = pd.DataFrame({
        "Spread":     spread,
        "Position":   position,
        "Daily_PnL":  daily_pnl,
        "Cum_PnL":    daily_pnl.cumsum(),
        "Equity":     initial_capital + daily_pnl.cumsum(),
    })
    return result.dropna()


# ── Performance Metrics ───────────────────────────────────────────────────────

def performance_metrics(bt: pd.DataFrame, rf: float = 0.05) -> dict:
    """
    Compute standard performance metrics from backtest results.
    rf: annualised risk-free rate (default 5% — approximate USD 2024 rate)
    """
    daily_ret = bt["Daily_PnL"] / bt["Equity"].shift(1)
    daily_ret = daily_ret.dropna().replace([np.inf, -np.inf], np.nan).dropna()

    ann_return  = daily_ret.mean() * 252
    ann_vol     = daily_ret.std()  * np.sqrt(252)
    sharpe      = (ann_return - rf) / ann_vol if ann_vol > 0 else np.nan

    running_max = bt["Equity"].cummax()
    drawdown    = (bt["Equity"] - running_max) / running_max
    max_dd      = drawdown.min()

    trades      = bt["Position"].diff().abs() / 2
    n_trades    = int(trades.sum())
    wins        = (bt["Daily_PnL"] > 0).sum()
    losses      = (bt["Daily_PnL"] < 0).sum()
    win_rate    = wins / (wins + losses) if (wins + losses) > 0 else np.nan

    total_pnl   = bt["Cum_PnL"].iloc[-1]
    calmar      = ann_return / abs(max_dd) if max_dd != 0 else np.nan

    return {
        "Total P&L ($)":        round(total_pnl, 2),
        "Annualised Return":    f"{ann_return:.2%}",
        "Annualised Volatility":f"{ann_vol:.2%}",
        "Sharpe Ratio":         round(sharpe, 2),
        "Max Drawdown":         f"{max_dd:.2%}",
        "Calmar Ratio":         round(calmar, 2),
        "Win Rate":             f"{win_rate:.2%}",
        "Num Trades":           n_trades,
    }


# ── Multi-Spread Signal Report ────────────────────────────────────────────────

def run_signal_report(spreads_with_z: pd.DataFrame,
                      entry_z: float = 1.5,
                      exit_z: float  = 0.5) -> dict:
    """
    Run backtest for WTI-Brent spread and 3-2-1 crack spread.
    Returns dict of {spread_name: (backtest_df, metrics_dict)}.
    """
    targets = {
        "WTI_Brent_Spread": "WTI_Brent_Spread_ZScore",
        "Crack_321":        "Crack_321_ZScore",
    }
    results = {}
    for spread_col, z_col in targets.items():
        sig = generate_signals(spreads_with_z[z_col], entry_z, exit_z)
        bt  = backtest(spreads_with_z[spread_col], sig)
        met = performance_metrics(bt)
        results[spread_col] = (bt, met)
    return results


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from src.data_fetcher   import fetch_prices
    from src.spread_analyzer import compute_spreads, add_zscore_signals

    df      = fetch_prices()
    spreads = add_zscore_signals(compute_spreads(df))
    report  = run_signal_report(spreads)

    for name, (bt, metrics) in report.items():
        print(f"\n{'='*50}")
        print(f"  {name}")
        print(f"{'='*50}")
        for k, v in metrics.items():
            print(f"  {k:<28}: {v}")
