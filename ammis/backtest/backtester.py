from typing import List, Dict

try:
    import pandas as pd
except Exception:
    pd = None

from ammis.engines.kronos_adapter import KronosAdapter
from ammis.execution.broker import ExecutionEngine, Order
from ammis.risk.engine import RiskEngine
from ammis.models.probabilities import ModelVote
from ammis.engines.market_math.aggregator import aggregate_votes
from ammis.engines.market_math.weights import OnlineWeighter
from ammis.core import db as dbcore


class SimpleBacktester:
    """A tiny backtester that uses KronosAdapter (mock when Kronos absent),
    aggregates model votes, applies simple risk checks, and simulates fills.

    This is intentionally small and deterministic so it can be used for
    demonstration and unit tests.
    """

    def __init__(self, adapter: KronosAdapter | None = None):
        self.adapter = adapter or KronosAdapter()
        self.exec = ExecutionEngine()
        self.risk = RiskEngine()
        self.weighter = OnlineWeighter()
        # attempt to load persisted scores
        try:
            scores = dbcore._db_client.load_model_scores()
            for m, s in scores.items():
                try:
                    self.weighter.set_score(m, float(s))
                except Exception:
                    pass
        except Exception:
            pass
        # optional metrics
        try:
            from prometheus_client import Counter, Histogram

            self.METRIC_BACKTEST_RUNS = Counter("ammis_backtest_runs_total", "Backtest runs")
            self.METRIC_BACKTEST_TRADES = Counter("ammis_backtest_trades_total", "Backtest trades executed")
            self.METRIC_BACKTEST_LATENCY = Histogram("ammis_backtest_latency_seconds", "Backtest run latency")
        except Exception:
            self.METRIC_BACKTEST_RUNS = None
            self.METRIC_BACKTEST_TRADES = None
            self.METRIC_BACKTEST_LATENCY = None

    def run(self, df: pd.DataFrame, lookback: int = 50, pred_len: int = 1) -> Dict:
        """Run a simple rolling backtest over `df`.

        df: DataFrame with columns ['open','high','low','close']
        lookback: number of historical bars to use for each forecast
        pred_len: forecast horizon (we use pred_len=1 for trade entry)
        """
        if not all(c in df.columns for c in ["open", "high", "low", "close"]):
            raise ValueError("DataFrame must contain open,high,low,close columns")

        trades = []
        pnl_series = []
        confidences = []

        if self.METRIC_BACKTEST_RUNS:
            self.METRIC_BACKTEST_RUNS.inc()

        if self.METRIC_BACKTEST_LATENCY:
            timer = self.METRIC_BACKTEST_LATENCY.time()
            timer.__enter__()
        try:
            # iterate over possible entry points
            for t in range(lookback, len(df) - pred_len):
                x_df = df.iloc[t - lookback : t][["open", "high", "low", "close"]]
                # get prediction(s)
                pred_df = self.adapter.predict(x_df, pred_len=pred_len)

                # create a mock ModelVote per adapter predict output
                # compute mean predicted close
                pred_mean = float(pred_df["close"].mean())
                last_close = float(x_df.iloc[-1]["close"])
                change = pred_mean - last_close
                # confidence: scale absolute change to 0..100 using a simple heuristic
                confidence = min(100.0, abs(change) / max(1e-8, last_close) * 1000.0)
                action = "HOLD"
                if change > 0:
                    action = "BUY"
                elif change < 0:
                    action = "SELL"

                vote = ModelVote(model="kronos_adapter", action=action, confidence=confidence)
                result = aggregate_votes([vote], threshold=0.0)  # don't threshold here

                confidences.append(result.overall_confidence)

                # risk check
                expected_loss = 0.5 * last_close  # simplistic placeholder
                if result.overall_action in {"BUY", "SELL"} and self.risk.approve(result.overall_action, expected_loss=expected_loss):
                    qty = 1.0
                    order = Order(action=result.overall_action, symbol="SIM", quantity=qty)
                    fill = self.exec.submit(order)
                    # compute realized PnL using actual future close at t+pred_len
                    future_close = float(df.iloc[t + pred_len]["close"])
                    if result.overall_action == "BUY":
                        pnl = (future_close - fill["filled_price"]) * qty
                    else:
                        pnl = (fill["filled_price"] - future_close) * qty

                    trades.append({"t": t, "order": order, "fill": fill, "pnl": pnl, "confidence": result.overall_confidence})
                    pnl_series.append(pnl)
                    if self.METRIC_BACKTEST_TRADES:
                        self.METRIC_BACKTEST_TRADES.inc()
                    # record loss into risk engine if negative
                    if pnl < 0:
                        self.risk.record_loss(abs(pnl))
                    # update online weighter with feedback (realized action)
                    try:
                        # provide the original vote to the weighter
                        self.weighter.update_from_feedback([vote], realized_action=('BUY' if pnl > 0 and result.overall_action=='BUY' else ('SELL' if pnl > 0 and result.overall_action=='SELL' else result.overall_action)))
                        # persist scores
                        try:
                            dbcore._db_client.save_model_scores(self.weighter._ema_loss)
                        except Exception:
                            pass
                    except Exception:
                        pass

        finally:
            if self.METRIC_BACKTEST_LATENCY:
                timer.__exit__(None, None, None)

        total_pnl = sum(pnl_series)
        avg_conf = float(sum(confidences) / len(confidences)) if confidences else 0.0

        return {
            "trades": trades,
            "total_pnl": total_pnl,
            "trade_count": len(trades),
            "avg_confidence": avg_conf,
        }
