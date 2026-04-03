# Crude Spread Analyzer

> A quantitative framework for monitoring, analysing, and trading crude
> oil and refined product spreads — including the **WTI–Brent location
> arbitrage** and the **3-2-1 crack spread** refinery margin.

------------------------------------------------------------------------

## Overview

Energy traders and analysts track two fundamental spread relationships
daily:

| Spread | What it measures |
|------------------------------------|------------------------------------|
| **WTI – Brent** | Location & quality arb between the US benchmark and the global seaborne benchmark |
| **3-2-1 Crack Spread** | Refinery gross margin proxy: `(2×Gasoline + 1×Diesel − 3×Crude) / 3` |
| **Gasoline Crack (1-1)** | Gasoline-specific refinery margin |
| **Diesel / ULSD Crack (1-1)** | Diesel / jet fuel proxy refinery margin |

This project provides a full analytical pipeline:

```         
Data Fetch → Spread Computation → Statistical Tests → Signal Generation → Backtest → Visualisation
```

------------------------------------------------------------------------

## Key Results (2019–2024 Backtest)

### WTI–Brent Cointegration

Engle-Granger cointegration test confirms the two benchmarks are
**cointegrated** (p = 0.029 \< 0.05), validating the statistical basis
for mean-reversion trading of the WTI–Brent differential.

### 3-2-1 Crack Spread Strategy

A z-score-based mean-reversion strategy on the crack spread (entry at
±1.5σ, exit at ±0.5σ) over the same period:

| Metric                | Value     |
|-----------------------|-----------|
| Annualised Return     | **67.6%** |
| Annualised Volatility | 24.6%     |
| **Sharpe Ratio**      | **2.55**  |
| Max Drawdown          | -8.81%    |
| **Calmar Ratio**      | **7.67**  |
| Win Rate              | 71.8%     |
| Number of Trades      | 189       |

### Crack Spread Statistics (2019–2024)

| Metric        | 3-2-1 Crack | Gasoline Crack | Diesel Crack |
|---------------|-------------|----------------|--------------|
| Mean (\$/bbl) | 20.20       | 18.07          | 24.46        |
| Std Dev       | 4.60        | 6.52           | 5.15         |
| Min           | 8.32        | 1.52           | 9.12         |
| Max           | 32.70       | 34.98          | 40.47        |

------------------------------------------------------------------------

## Project Structure

```         
crude-spread-analyzer/
│
├── main.py                     # End-to-end pipeline runner
├── requirements.txt
│
├── src/
│   ├── data_fetcher.py         # Yahoo Finance data ingestion (WTI, Brent, RBOB, ULSD)
│   ├── spread_analyzer.py      # Spread computation, cointegration, ADF tests, rolling corr
│   ├── signals.py              # Z-score signal generation, backtest engine, performance metrics
│   └── visualizer.py           # Interactive Plotly dashboards
│
├── data/
│   └── prices.csv              # Cached price data (auto-generated on first run)
│
└── reports/
    ├── 01_crude_prices.html
    ├── 02_wti_brent_spread.html   ← spread + z-score + signal markers
    ├── 03_crack_spread.html       ← refinery margin regimes
    ├── 04_product_cracks.html     ← gasoline vs diesel vs 3-2-1
    ├── 05_rolling_correlation.html
    └── 06_pnl_comparison.html
```

------------------------------------------------------------------------

## Methodology

### 1. Data

Prices are sourced from Yahoo Finance via `yfinance`:

| Instrument               | Ticker | Unit                             |
|--------------------------|--------|----------------------------------|
| WTI Crude Oil            | `CL=F` | \$/bbl                           |
| Brent Crude Oil          | `BZ=F` | \$/bbl                           |
| RBOB Gasoline            | `RB=F` | \$/gal → converted ×42 to \$/bbl |
| Heating Oil (ULSD proxy) | `HO=F` | \$/gal → converted ×42 to \$/bbl |

### 2. Spread Calculations

``` python
WTI_Brent_Spread  = WTI − Brent
Crack_321         = (2 × Gasoline + Diesel − 3 × WTI) / 3
Gasoline_Crack    = Gasoline − WTI
Diesel_Crack      = Diesel − WTI
```

The **3-2-1** ratio reflects a simplified refinery slate: for every 3
barrels of crude processed, a typical refinery yields roughly 2 barrels
of gasoline and 1 barrel of distillate (diesel/jet fuel).

### 3. Statistical Analysis

**Cointegration (Engle-Granger):** Tests whether WTI and Brent share a
long-run equilibrium. Rejection of the null (p \< 0.05) implies the
spread is mean-reverting and statistically tradeable.

**Augmented Dickey-Fuller (ADF):** Tests individual spread stationarity.
A stationary spread (I(0)) can be traded with confidence that it returns
to its mean.

**Rolling Correlation:** 60-day Pearson correlation between WTI crude
and the 3-2-1 crack spread identifies regimes where refinery demand is
decoupling from crude supply drivers.

### 4. Signal Generation

``` python
# Z-score computed over a 60-day rolling window
z = (spread − rolling_mean) / rolling_std

# Entry / exit rules
if z > +1.5 → SHORT the spread (too wide, expect compression)
if z < −1.5 → LONG the spread  (too tight, expect expansion)
if |z| < 0.5 → EXIT position   (mean reversion achieved)
```

This mirrors how traders on energy desks monitor and exploit short-term
deviations from fair value.

### 5. Backtest

-   Daily rebalancing, no look-ahead bias (signals are lagged by 1 day)
-   P&L computed as: `position[t−1] × ΔSpread[t]`
-   Risk-free rate: 5% annualised (approximate 2024 USD rate)
-   No transaction costs (can be layered in)

------------------------------------------------------------------------

## Quick Start

``` bash
git clone https://github.com/OwenWang19/crude-spread-analyzer.git
cd crude-spread-analyzer
pip install -r requirements.txt

# Run the full pipeline (fetches live data, generates charts)
python main.py

# Custom date range
python main.py --start 2021-01-01

# Analysis only, no HTML exports
python main.py --no-plots
```

Open any file in `reports/` in your browser for interactive charts.

------------------------------------------------------------------------

## Visualisations

All charts are built with **Plotly** and saved as self-contained
interactive HTML files.

| Chart | Description |
|------------------------------------|------------------------------------|
| `01_crude_prices.html` | WTI vs Brent price history |
| `02_wti_brent_spread.html` | Spread + rolling z-score + long/short signal markers + equity curve |
| `03_crack_spread.html` | 3-2-1 crack spread with above/below-median regime colouring + equity curve |
| `04_product_cracks.html` | Gasoline, diesel, and composite crack spread overlay |
| `05_rolling_correlation.html` | 60-day rolling correlation: crude vs crack |
| `06_pnl_comparison.html` | Cumulative P&L: WTI–Brent arb vs crack spread arb |

------------------------------------------------------------------------

## Market Context

The WTI–Brent differential is driven by: - **US production & export
capacity** (shale output, Gulf Coast terminal congestion) -
**Transportation costs** (pipeline tariffs, tanker rates) -
**Geopolitical events** (sanctions, OPEC+ cuts affecting Brent-quality
barrels)

The crack spread is driven by: - **Refinery utilisation** (turnaround
seasons, unplanned outages) - **Seasonal demand** (gasoline driving
season Apr–Aug; heating oil Oct–Feb) - **Product inventory levels** (EIA
weekly draws/builds in PADD regions) - **Crude quality differentials**
(light-sweet vs heavy-sour processing economics)

------------------------------------------------------------------------

## Dependencies

```         
yfinance>=0.2.40
pandas>=2.0.0
numpy>=1.26.0
statsmodels>=0.14.0
plotly>=5.20.0
scipy>=1.12.0
```

------------------------------------------------------------------------

## Further Work

-   [ ] Incorporate EIA weekly supply/demand data (crude inventories,
    refinery utilisation %)
-   [ ] Add regime detection (HMM) to identify high/low crack spread
    environments
-   [ ] Extend to include Singapore complex margins (Singapore 5-3-2
    crack)
-   [ ] Add transaction cost modelling and slippage assumptions
-   [ ] Build a real-time monitoring dashboard with auto-refresh

------------------------------------------------------------------------

## Author

**Jiashu Wang** — MSc Statistics & Data Science, National University of
Singapore\
[GitHub](https://github.com/OwenWang19) \|
[LinkedIn](https://www.linkedin.com/in/jiashu-wang-8022b6309/)
