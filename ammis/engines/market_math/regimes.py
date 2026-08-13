"""Regime detection utilities (GMM-based with sklearn fallback).

Provides a small interface to fit/predict regimes from feature matrices.
"""
from typing import Optional

try:
    from sklearn.mixture import GaussianMixture
    import numpy as np
except Exception:
    GaussianMixture = None
    np = None


class RegimeDetector:
    def __init__(self, n_states: int = 2, random_state: int = 0):
        self.n_states = n_states
        self.random_state = random_state
        self._model = None

    def fit(self, X) -> 'RegimeDetector':
        if GaussianMixture is None:
            raise RuntimeError("sklearn not available: cannot fit RegimeDetector")
        arr = X if np is None else np.asarray(X)
        gm = GaussianMixture(n_components=self.n_states, random_state=self.random_state)
        gm.fit(arr)
        self._model = gm
        return self

    def predict(self, X) -> list:
        if self._model is None:
            raise RuntimeError("RegimeDetector not fitted")
        arr = X if np is None else np.asarray(X)
        return list(self._model.predict(arr))

    def predict_proba(self, X) -> list:
        if self._model is None:
            raise RuntimeError("RegimeDetector not fitted")
        arr = X if np is None else np.asarray(X)
        return list(self._model.predict_proba(arr))


def quick_sample_detection(returns_series, n_states: int = 2) -> Optional[list]:
    """Fit a quick GMM to the 1D returns series and return regime labels.

    returns_series: iterable of floats
    """
    if GaussianMixture is None:
        return None
    X = np.array(returns_series).reshape(-1, 1)
    rd = RegimeDetector(n_states=n_states)
    rd.fit(X)
    return rd.predict(X)
