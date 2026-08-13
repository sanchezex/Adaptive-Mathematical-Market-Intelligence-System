from typing import Callable, Dict, Iterable, List

try:
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression
    import numpy as np
except Exception:
    IsotonicRegression = None
    LogisticRegression = None
    np = None


class BaseCalibrator:
    def fit(self, probs: Iterable[float], y: Iterable[int]):
        raise NotImplementedError()

    def transform(self, probs: Iterable[float]) -> List[float]:
        raise NotImplementedError()


class IdentityCalibrator(BaseCalibrator):
    def fit(self, probs, y):
        return self

    def transform(self, probs):
        return [float(p) for p in probs]


class PlattCalibrator(BaseCalibrator):
    def __init__(self):
        self._model = None

    def fit(self, probs, y):
        if LogisticRegression is None:
            # fallback: no-op
            return IdentityCalibrator()
        X = [[p] for p in probs]
        clf = LogisticRegression(solver='lbfgs')
        clf.fit(X, y)
        self._model = clf
        return self

    def transform(self, probs):
        if self._model is None:
            return [float(p) for p in probs]
        X = [[p] for p in probs]
        return [float(x[0]) for x in self._model.predict_proba(X)[:, 1]]


class IsotonicCalibrator(BaseCalibrator):
    def __init__(self):
        self._model = None

    def fit(self, probs, y):
        if IsotonicRegression is None:
            return IdentityCalibrator()
        self._model = IsotonicRegression(out_of_bounds='clip')
        self._model.fit(list(probs), list(y))
        return self

    def transform(self, probs):
        if self._model is None:
            return [float(p) for p in probs]
        return [float(x) for x in self._model.transform(list(probs))]


# Simple registry for per-model calibrators
_REGISTRY: Dict[str, BaseCalibrator] = {}


def register_calibrator(model_name: str, calibrator: BaseCalibrator) -> None:
    _REGISTRY[model_name] = calibrator


def get_calibrator(model_name: str) -> BaseCalibrator:
    return _REGISTRY.get(model_name, IdentityCalibrator())


def calibrate_votes(votes, y=None):
    """Calibrate a list of votes in-place or return calibrated confidences.

    votes: iterable of objects with `model` and `confidence` (0..100 or 0..1)
    y: optional iterable of ground-truth labels (0/1) to fit calibrator for models
    """
    # group by model
    by_model = {}
    for v in votes:
        by_model.setdefault(v.model, []).append(v)

    results = []
    for model, lst in by_model.items():
        cal = get_calibrator(model)
        probs = [v.confidence / 100.0 for v in lst]
        if y is not None:
            # user-supplied labels must align; naive: reuse same labels for all
            cal = cal.fit(probs, y)
        calibrated = cal.transform(probs)
        for v, c in zip(lst, calibrated):
            v.confidence = float(c * 100.0)
            results.append(v)

    return results
