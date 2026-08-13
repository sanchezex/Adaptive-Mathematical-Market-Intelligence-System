"""Scaffold for integrating Backtrader or vectorbt with AMMIS backtester.

This file provides function signatures and notes for where to plug in
real backtesting libraries without pulling heavy dependencies into the core.
"""

def to_backtrader_feed(df):
    """Convert OHLCV df to backtrader feed. Implement when backtrader is added."""
    raise NotImplementedError("Install backtrader and implement conversion")

def run_backtrader_strategy(strategy_cls, datafeed):
    """Run a backtrader strategy and return results. Placeholder."""
    raise NotImplementedError("Integrate backtrader runner here")
