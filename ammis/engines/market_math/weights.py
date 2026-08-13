from typing import Dict, Iterable, List, Optional
from collections import defaultdict

from ammis.models.probabilities import ModelVote, Action


class OnlineWeighter:
    """Online per-model weighter using exponential moving average of Brier score.

    Lower recent Brier score => higher weight. Weights are scaled to sum to 1.
    """

    def __init__(self, decay: float = 0.98, init_score: float = 0.25):
        self.decay = float(decay)
        # EMA of loss per model
        self._ema_loss: Dict[str, float] = defaultdict(lambda: float(init_score))

    def update_from_feedback(self, votes: Iterable[ModelVote], realized_action: Action) -> None:
        """Update EMA losses using the provided votes and the realized action.

        Each vote is treated as a probability for its action; target is 1 if the
        vote's action equals the realized_action, else 0. Uses Brier score.
        """
        for v in votes:
            p = float(v.confidence) / 100.0
            y = 1.0 if v.action == realized_action else 0.0
            brier = (p - y) ** 2
            prev = self._ema_loss.get(v.model, brier)
            ema = self.decay * prev + (1.0 - self.decay) * brier
            self._ema_loss[v.model] = ema

    def get_weights(self, models: Optional[Iterable[str]] = None) -> Dict[str, float]:
        """Return normalized weights for given models. If models is None, return
        weights for all seen models.
        """
        if models is None:
            models = list(self._ema_loss.keys())

        # Convert EMA losses to scores; smaller loss -> larger score
        eps = 1e-8
        raw = {}
        for m in models:
            loss = float(self._ema_loss.get(m, 0.25))
            raw[m] = 1.0 / (loss + eps)

        total = sum(raw.values())
        if total <= 0:
            # fallback uniform
            models = list(raw.keys())
            n = len(models) or 1
            return {m: 1.0 / n for m in models}

        return {m: raw[m] / total for m in raw}

    def set_score(self, model: str, ema_loss: float) -> None:
        self._ema_loss[model] = float(ema_loss)

    def get_score(self, model: str) -> float:
        return float(self._ema_loss.get(model, 0.25))
