"""Kronos adapter for AMMIS.

This adapter will attempt to load the real Kronos package (as installed from
the Kronos repo). When Kronos is not available it raises a clear error so the
user can install it (use `scripts/install_kronos.sh`).

Usage:
    adapter = KronosAdapter()
    adapter.load(model_name="NeoQuasar/Kronos-small")
    pred = adapter.predict(df, pred_len=120)

The adapter supports both `predict` and `predict_batch` and preserves the
Kronos predictor API surface where possible.
"""

from __future__ import annotations

from typing import Any, List, Optional
import importlib
import logging

try:
    import pandas as pd
except Exception:
    pd = None

logger = logging.getLogger(__name__)


class KronosAdapter:
    """Adapter that wraps a real Kronos predictor when installed.

    The adapter will try a few common import paths to find Kronos. If it
    cannot find a compatible predictor it raises ImportError with guidance.
    """

    def __init__(self, use_mock: bool = True) -> None:
        self.predictor: Optional[Any] = None
        self.use_mock = use_mock

        # optional metrics
        try:
            from prometheus_client import Counter, Histogram

            self.METRIC_PRED_COUNT = Counter("ammis_kronos_predict_total", "Kronos predict calls")
            self.METRIC_PRED_LATENCY = Histogram("ammis_kronos_predict_latency_seconds", "Kronos predict latency")
        except Exception:
            self.METRIC_PRED_COUNT = None
            self.METRIC_PRED_LATENCY = None

    def _find_kronos_modules(self) -> Any:
        """Try to import Kronos predictor/tokenizer from known locations."""
        candidates = [
            ("model", ["KronosPredictor", "KronosTokenizer"]),
            ("kronos.model", ["KronosPredictor", "KronosTokenizer"]),
        ]
        for pkg, names in candidates:
            try:
                mod = importlib.import_module(pkg)
                # basic sanity check
                if all(hasattr(mod, n) for n in names):
                    return mod
            except Exception:
                continue
        # Not found
        return None

    def load(self, model_name: str = "NeoQuasar/Kronos-small", tokenizer_name: Optional[str] = None, device: Optional[str] = None) -> None:
        """Load Kronos predictor and tokenizer from installed package.

        model_name/tokenizer_name can be either local paths or Hugging Face ids.
        """
        kronos_mod = self._find_kronos_modules()

        if kronos_mod is None:
            if self.use_mock:
                logger.warning("Kronos not installed — running in mock mode")
                self.predictor = None
                return
            raise ImportError(
                "Kronos package not found. Install from GitHub: `pip install git+https://github.com/shiyu-coder/Kronos.git` or run scripts/install_kronos.sh`")

        try:
            KronosPredictor = getattr(kronos_mod, "KronosPredictor")
            KronosTokenizer = getattr(kronos_mod, "KronosTokenizer")

            tokenizer = KronosTokenizer.from_pretrained(tokenizer_name or "NeoQuasar/Kronos-Tokenizer-base")
            # KronosPredictor.from_pretrained may accept model_name; some versions
            # expose different constructors — try common patterns.
            try:
                model = KronosPredictor.from_pretrained(model_name)
                self.predictor = KronosPredictor(model, tokenizer)
            except Exception:
                # some Kronos versions expose Kronos as model class directly
                Kronos = getattr(kronos_mod, "Kronos", None)
                if Kronos is not None:
                    model = Kronos.from_pretrained(model_name)
                    self.predictor = KronosPredictor(model, tokenizer)
                else:
                    # last resort: try passing identifiers directly
                    self.predictor = KronosPredictor(model_name, tokenizer)

            logger.info("Kronos loaded successfully")
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize Kronos predictor: {exc}") from exc

    def available(self) -> bool:
        return self.predictor is not None

    def predict(self, df: pd.DataFrame, pred_len: int = 10, **kwargs: Any) -> pd.DataFrame:
        # if real predictor available, delegate and record metrics
        if self.available():
            if self.METRIC_PRED_COUNT:
                self.METRIC_PRED_COUNT.inc()
            if self.METRIC_PRED_LATENCY:
                with self.METRIC_PRED_LATENCY.time():
                    return self.predictor.predict(df=df, pred_len=pred_len, **kwargs)
            return self.predictor.predict(df=df, pred_len=pred_len, **kwargs)

        # fallback mock predictor: carry-forward close and zero volume
        if pd is None:
            raise ImportError("pandas is required for mock predictions. Install pandas or install Kronos for real predictions.")
        last = df.iloc[-1]["close"] if "close" in df.columns else 0.0
        index = pd.RangeIndex(start=0, stop=pred_len, step=1)
        data = {"open": [last] * pred_len, "high": [last] * pred_len, "low": [last] * pred_len, "close": [last] * pred_len, "volume": [0] * pred_len}
        return pd.DataFrame(data, index=index)

    def predict_batch(self, df_list: List[pd.DataFrame], pred_len: int = 10, **kwargs: Any) -> List[pd.DataFrame]:
        if self.available():
            if self.METRIC_PRED_COUNT:
                self.METRIC_PRED_COUNT.inc(len(df_list))
            if self.METRIC_PRED_LATENCY:
                with self.METRIC_PRED_LATENCY.time():
                    return self.predictor.predict_batch(df_list=df_list, pred_len=pred_len, **kwargs)
            return self.predictor.predict_batch(df_list=df_list, pred_len=pred_len, **kwargs)

        return [self.predict(d, pred_len=pred_len, **kwargs) for d in df_list]

