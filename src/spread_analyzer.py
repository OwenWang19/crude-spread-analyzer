"""
spread_analyzer.py
------------------
Computes the key spreads watched by energy traders:

  1. WTI–Brent Spread         → location/quality arb between US & global crude benchmarks
  2. 3-2-1 Crack Spread       → refinery gross margin proxy (3 bbl crude → 2 bbl gasoline + 1 bbl diesel)
  3. Gasoline Crack (1-1)     → gasoline-specific refinery margin
  4. Diesel Crack (1-1)       → diesel/ULSD-specific refinery margin

Statistical analysis:
  - Rolling mean & std (z-score normalisation)
  - Engle-Granger cointegration test (WTI vs Brent)
  - Augmented Dickey-Fuller stationarity test on spreads
  - Rolling correlation between crack spread and crude price
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint, adfuller


# ── Spread Calculations ──────────────────────────────────────────────────────

def compute_spreads(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input : DataFrame with columns [WTI, Brent, Gasoline, Diesel] in $/bbl
    Output: DataFrame with all spreads in $/bbl
    """
    spreads = pd.DataFrame(index=df.index)
    spreads["WTI_Brent_Spread"]   = df["WTI"] - df["Brent"]
    spreads["Crack_321"]          = (2 * df["Gasoline"] + df["Diesel"] - 3 * df["WTI"]) / 3
    spreads["Gasoline_Crack"]     = df["Gasoline"] - df["WTI"]
    spreads["Diesel_Crack"]       = df["Diesel"] - df["WTI"]
    return spreads


# ── Rolling Z-Score ───────────────────────────────────────────────────────────

def rolling_zscore(series: pd.Series, window: int = 60) -> pd.Series:
    """
    Compute z-score of a spread relative to its rolling mean/std.
    Window = 60 trading days (~3 months) is typical for energy desks.
    """
    mu  = series.rolling(window).mean()
    sig = series.rolling(window).std()
    return (series - mu) / sig


def add_zscore_signals(spreads: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """Append z-score columns for each spread."""
    out = spreads.copy()
    for col in spreads.columns:
        out[f"{col}_ZScore"] = rolling_zscore(spreads[col], window)
    return out


# ── Statistical Tests ─────────────────────────────────────────────────────────

def cointegration_test(df: pd.DataFrame) -> dict:
    """
    Engle-Granger cointegration test: WTI vs Brent.
    Null hypothesis: no cointegration.
    Rejection (p < 0.05) → spread is mean-reverting → tradeable arb.
    """
    clean = df[["WTI", "Brent"]].dropna()
    score, pvalue, crit = coint(clean["WTI"], clean["Brent"])
    return {
        "test":    "Engle-Granger Cointegration (WTI vs Brent)",
        "t-stat":  round(score, 4),
        "p-value": round(pvalue, 4),
        "crit_1%": round(crit[0], 4),
        "crit_5%": round(crit[1], 4),
        "result":  "Cointegrated ✓ (mean-reverting arb exists)" if pvalue < 0.05
                   else "Not cointegrated ✗",
    }


def adf_test(series: pd.Series, name: str = "") -> dict:
    """
    Augmented Dickey-Fuller test for stationarity.
    A stationary spread (p < 0.05) is more reliably mean-reverting.
    """
    result = adfuller(series.dropna(), autolag="AIC")
    return {
        "series":  name,
        "adf-stat": round(result[0], 4),
        "p-value":  round(result[1], 4),
        "lags":     result[2],
        "result":   "Stationary ✓" if result[1] < 0.05 else "Non-stationary ✗",
    }


def run_all_stationarity_tests(spreads: pd.DataFrame) -> pd.DataFrame:
    """Run ADF on all spread series and return a summary table."""
    base_cols = [c for c in spreads.columns if "ZScore" not in c]
    rows = [adf_test(spreads[col], col) for col in base_cols]
    return pd.DataFrame(rows).set_index("series")


# ── Rolling Correlation ───────────────────────────────────────────────────────

def rolling_crack_vs_crude(df: pd.DataFrame, spreads: pd.DataFrame,
                            window: int = 60) -> pd.DataFrame:
    """
    Rolling correlation between the 3-2-1 crack spread and WTI crude price.
    Helps identify regimes where refinery margins decouple from crude.
    """
    combined = pd.concat([df["WTI"], spreads["Crack_321"]], axis=1).dropna()
    return combined["WTI"].rolling(window).corr(combined["Crack_321"]).rename(
        "WTI_vs_Crack321_Corr"
    )


# ── Summary Statistics ────────────────────────────────────────────────────────

def summary_stats(spreads: pd.DataFrame) -> pd.DataFrame:
    """Descriptive statistics for all base spreads."""
    base_cols = [c for c in spreads.columns if "ZScore" not in c]
    stats = spreads[base_cols].describe().T
    stats["skewness"] = spreads[base_cols].skew()
    stats["kurtosis"] = spreads[base_cols].kurt()
    return stats.round(2)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from src.data_fetcher import fetch_prices

    df      = fetch_prices()
    spreads = compute_spreads(df)
    spreads = add_zscore_signals(spreads)

    print("=== Spread Summary Stats ===")
    print(summary_stats(spreads))

    print("\n=== Cointegration Test ===")
    coint_res = cointegration_test(df)
    for k, v in coint_res.items():
        print(f"  {k}: {v}")

    print("\n=== ADF Stationarity Tests ===")
    print(run_all_stationarity_tests(spreads))
