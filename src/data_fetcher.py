"""
data_fetcher.py
---------------
Fetches energy futures prices from Yahoo Finance.

Tickers used:
  CL=F  → WTI Crude Oil ($/bbl)
  BZ=F  → Brent Crude Oil ($/bbl)
  RB=F  → RBOB Gasoline ($/gal) — converted to $/bbl (×42)
  HO=F  → Heating Oil / ULSD Diesel proxy ($/gal) — converted to $/bbl (×42)
"""

import yfinance as yf
import pandas as pd

TICKERS = {
    "WTI":      "CL=F",
    "Brent":    "BZ=F",
    "Gasoline": "RB=F",   # $/gal → need ×42
    "Diesel":   "HO=F",   # $/gal → need ×42
}

GALLON_TICKERS = {"Gasoline", "Diesel"}
BARRELS_PER_GALLON = 42


def fetch_prices(start: str = "2019-01-01", end: str = None) -> pd.DataFrame:
    """
    Download daily close prices for WTI, Brent, RBOB Gasoline, and ULSD Diesel.
    Returns a DataFrame with columns [WTI, Brent, Gasoline, Diesel] in $/bbl.
    """
    raw = yf.download(
        list(TICKERS.values()),
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
    )["Close"]

    # Rename columns from ticker to friendly name
    inv = {v: k for k, v in TICKERS.items()}
    raw = raw.rename(columns=inv)

    # Convert $/gal → $/bbl for refinery products
    for col in GALLON_TICKERS:
        if col in raw.columns:
            raw[col] = raw[col] * BARRELS_PER_GALLON

    df = raw[list(TICKERS.keys())].dropna()
    df.index = pd.to_datetime(df.index)
    df.index.name = "Date"
    return df


def load_from_csv(path: str = "data/prices.csv") -> pd.DataFrame:
    """Load pre-saved prices from CSV (useful for offline / backtesting)."""
    df = pd.read_csv(path, index_col="Date", parse_dates=True)
    df.index.name = "Date"
    return df


if __name__ == "__main__":
    df = fetch_prices()
    print(df.tail())
    print(f"\nShape: {df.shape}")
    print(f"Date range: {df.index[0].date()} → {df.index[-1].date()}")
