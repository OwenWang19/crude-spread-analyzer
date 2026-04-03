"""
visualizer.py
-------------
Interactive Plotly charts for the crude spread analysis dashboard.

Charts produced:
  1. Crude benchmarks: WTI vs Brent price history
  2. WTI–Brent spread + rolling z-score + signal overlay
  3. 3-2-1 crack spread + refinery margin regimes
  4. Gasoline vs Diesel crack comparison
  5. Rolling WTI-vs-crack correlation
  6. Cumulative P&L comparison (WTI-Brent arb vs Crack spread arb)
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ── Colour Palette ─────────────────────────────────────────────────────────────
COLOURS = {
    "WTI":      "#1f77b4",
    "Brent":    "#d62728",
    "Gasoline": "#2ca02c",
    "Diesel":   "#ff7f0e",
    "Spread":   "#9467bd",
    "Crack":    "#e377c2",
    "ZScore":   "#7f7f7f",
    "Long":     "#00b300",
    "Short":    "#cc0000",
    "PnL":      "#1f77b4",
}

LAYOUT_DEFAULTS = dict(
    template="plotly_white",
    font=dict(family="Inter, sans-serif", size=12),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


# ── Plot 1: Crude Benchmark Prices ────────────────────────────────────────────

def plot_crude_prices(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col, colour in [("WTI", COLOURS["WTI"]), ("Brent", COLOURS["Brent"])]:
        fig.add_trace(go.Scatter(
            x=df.index, y=df[col], name=col,
            line=dict(color=colour, width=1.5),
        ))
    fig.update_layout(
        title="WTI vs Brent Crude Oil — Daily Close ($/bbl)",
        yaxis_title="Price ($/bbl)",
        **LAYOUT_DEFAULTS,
    )
    return fig


# ── Plot 2: WTI–Brent Spread + Z-Score + Signals ─────────────────────────────

def plot_wti_brent_spread(spreads: pd.DataFrame, bt: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.45, 0.30, 0.25],
        subplot_titles=(
            "WTI–Brent Spread ($/bbl)",
            "Rolling Z-Score (60-day window)",
            "Strategy Equity Curve ($)",
        ),
        vertical_spacing=0.06,
    )

    # ── Row 1: Spread + signal markers
    fig.add_trace(go.Scatter(
        x=spreads.index, y=spreads["WTI_Brent_Spread"],
        name="WTI-Brent Spread", line=dict(color=COLOURS["Spread"], width=1.5),
    ), row=1, col=1)

    long_entries  = bt[(bt["Position"] == 1)  & (bt["Position"].shift(1) != 1)]
    short_entries = bt[(bt["Position"] == -1) & (bt["Position"].shift(1) != -1)]

    fig.add_trace(go.Scatter(
        x=long_entries.index, y=spreads.loc[long_entries.index, "WTI_Brent_Spread"],
        mode="markers", name="Long Entry",
        marker=dict(symbol="triangle-up", size=9, color=COLOURS["Long"]),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=short_entries.index, y=spreads.loc[short_entries.index, "WTI_Brent_Spread"],
        mode="markers", name="Short Entry",
        marker=dict(symbol="triangle-down", size=9, color=COLOURS["Short"]),
    ), row=1, col=1)

    # ── Row 2: Z-score + threshold lines
    fig.add_trace(go.Scatter(
        x=spreads.index, y=spreads["WTI_Brent_Spread_ZScore"],
        name="Z-Score", line=dict(color=COLOURS["ZScore"], width=1),
    ), row=2, col=1)
    for level, dash in [(1.5, "dot"), (-1.5, "dot"), (0.5, "dash"), (-0.5, "dash")]:
        fig.add_hline(y=level, line_dash=dash, line_color="grey",
                      line_width=0.8, row=2, col=1)

    # ── Row 3: Equity curve
    fig.add_trace(go.Scatter(
        x=bt.index, y=bt["Equity"],
        name="Strategy Equity", line=dict(color=COLOURS["PnL"], width=1.5),
        fill="tozeroy", fillcolor="rgba(31,119,180,0.08)",
    ), row=3, col=1)

    fig.update_layout(
        title="WTI–Brent Spread Analysis & Mean-Reversion Strategy",
        height=750,
        **LAYOUT_DEFAULTS,
    )
    fig.update_yaxes(title_text="$/bbl", row=1, col=1)
    fig.update_yaxes(title_text="Z-Score", row=2, col=1)
    fig.update_yaxes(title_text="Equity ($)", row=3, col=1)
    return fig


# ── Plot 3: 3-2-1 Crack Spread ────────────────────────────────────────────────

def plot_crack_spread(spreads: pd.DataFrame, bt: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.4],
        subplot_titles=(
            "3-2-1 Crack Spread — Refinery Gross Margin ($/bbl)",
            "Crack Spread Strategy Equity Curve ($)",
        ),
        vertical_spacing=0.08,
    )

    # Colour the crack spread by regime (high/low margin)
    crack = spreads["Crack_321"]
    median_crack = crack.median()
    colours_series = [COLOURS["Gasoline"] if v >= median_crack
                      else COLOURS["Short"] for v in crack]

    fig.add_trace(go.Bar(
        x=crack.index, y=crack.values,
        name="3-2-1 Crack Spread",
        marker_color=colours_series,
        opacity=0.7,
    ), row=1, col=1)
    fig.add_hline(y=median_crack, line_dash="dash", line_color="black",
                  line_width=1, annotation_text=f"Median: ${median_crack:.1f}",
                  row=1, col=1)

    fig.add_trace(go.Scatter(
        x=bt.index, y=bt["Equity"],
        name="Crack Arb Equity", line=dict(color=COLOURS["Crack"], width=1.5),
        fill="tozeroy", fillcolor="rgba(227,119,194,0.08)",
    ), row=2, col=1)

    fig.update_layout(
        title="3-2-1 Crack Spread — Refinery Margin Analysis & Arb Strategy",
        height=600,
        **LAYOUT_DEFAULTS,
    )
    fig.update_yaxes(title_text="$/bbl", row=1, col=1)
    fig.update_yaxes(title_text="Equity ($)", row=2, col=1)
    return fig


# ── Plot 4: Product Cracks Comparison ────────────────────────────────────────

def plot_product_cracks(spreads: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col, colour, name in [
        ("Gasoline_Crack", COLOURS["Gasoline"], "Gasoline Crack (1-1)"),
        ("Diesel_Crack",   COLOURS["Diesel"],   "Diesel / ULSD Crack (1-1)"),
        ("Crack_321",      COLOURS["Crack"],     "3-2-1 Composite Crack"),
    ]:
        fig.add_trace(go.Scatter(
            x=spreads.index, y=spreads[col],
            name=name, line=dict(color=colour, width=1.5),
        ))
    fig.update_layout(
        title="Gasoline vs Diesel vs 3-2-1 Crack Spreads ($/bbl)",
        yaxis_title="Crack Spread ($/bbl)",
        **LAYOUT_DEFAULTS,
    )
    return fig


# ── Plot 5: Rolling Correlation ───────────────────────────────────────────────

def plot_rolling_correlation(corr: pd.Series) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=corr.index, y=corr,
        name="Rolling Corr (WTI vs 3-2-1 Crack)",
        line=dict(color=COLOURS["ZScore"], width=1.5),
    ))
    fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=0.5)
    fig.update_layout(
        title="60-Day Rolling Correlation: WTI Crude Price vs 3-2-1 Crack Spread",
        yaxis_title="Pearson Correlation",
        yaxis=dict(range=[-1, 1]),
        **LAYOUT_DEFAULTS,
    )
    return fig


# ── Plot 6: P&L Comparison ────────────────────────────────────────────────────

def plot_pnl_comparison(bt_wb: pd.DataFrame, bt_crack: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=bt_wb.index, y=bt_wb["Cum_PnL"],
        name="WTI–Brent Arb", line=dict(color=COLOURS["WTI"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=bt_crack.index, y=bt_crack["Cum_PnL"],
        name="3-2-1 Crack Arb", line=dict(color=COLOURS["Crack"], width=2),
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="grey", line_width=0.8)
    fig.update_layout(
        title="Cumulative P&L Comparison — WTI–Brent Arb vs Crack Spread Arb",
        yaxis_title="Cumulative P&L ($)",
        **LAYOUT_DEFAULTS,
    )
    return fig


# ── Save All Figures ──────────────────────────────────────────────────────────

def save_all(figures: dict, output_dir: str = "reports") -> None:
    """Save all figures as interactive HTML files."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    for name, fig in figures.items():
        path = os.path.join(output_dir, f"{name}.html")
        fig.write_html(path)
        print(f"  Saved → {path}")
