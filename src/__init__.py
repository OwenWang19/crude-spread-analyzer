from .data_fetcher    import fetch_prices
from .spread_analyzer import compute_spreads, add_zscore_signals, cointegration_test, run_all_stationarity_tests, summary_stats, rolling_crack_vs_crude
from .signals         import run_signal_report
from .visualizer      import (plot_crude_prices, plot_wti_brent_spread,
                               plot_crack_spread, plot_product_cracks,
                               plot_rolling_correlation, plot_pnl_comparison,
                               save_all)
