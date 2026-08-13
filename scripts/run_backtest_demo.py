"""Run a tiny backtest demo using the SimpleBacktester."""
import numpy as np
import pandas as pd

from ammis.backtest.backtester import SimpleBacktester


def make_random_walk(n: int = 500, start: float = 100.0, vol: float = 1.0) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    steps = rng.normal(loc=0.0, scale=vol, size=n)
    price = start + np.cumsum(steps)
    df = pd.DataFrame({"open": price, "high": price + 0.1, "low": price - 0.1, "close": price})
    return df


def main() -> None:
    df = make_random_walk(400)
    bt = SimpleBacktester()
    res = bt.run(df, lookback=50, pred_len=1)
    print("Total PnL:", res["total_pnl"]) 
    print("Trade count:", res["trade_count"]) 
    print("Avg confidence:", res["avg_confidence"]) 


if __name__ == "__main__":
    main()
