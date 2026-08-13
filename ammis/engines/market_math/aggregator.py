from typing import Dict, List

from ammis.models.probabilities import Action, ConfidenceResult, ModelVote
from ammis.models.calibration import calibrate_votes
from typing import Optional


try:
    from ammis.engines.market_math.weights import OnlineWeighter
except Exception:
    OnlineWeighter = None


def aggregate_votes(votes: List[ModelVote], threshold: float = 80.0, weighter: Optional[OnlineWeighter] = None) -> ConfidenceResult:
    # Apply per-model calibration if available
    try:
        votes = calibrate_votes(votes)
    except Exception:
        # fallback to raw votes on any error
        pass
    # Compute per-model per-action average confidence
    by_model: Dict[str, Dict[Action, List[float]]] = {}
    for v in votes:
        by_model.setdefault(v.model, {"BUY": [], "SELL": [], "HOLD": []})
        by_model[v.model][v.action].append(v.confidence)

    # per-model average confidences
    model_action_avg: Dict[str, Dict[Action, float]] = {}
    for m, d in by_model.items():
        model_action_avg[m] = {a: (sum(vals) / len(vals) if vals else 0.0) for a, vals in d.items()}

    models = list(model_action_avg.keys())
    # get weights
    if weighter is None or OnlineWeighter is None:
        weights = {m: 1.0 / (len(models) or 1) for m in models}
    else:
        weights = weighter.get_weights(models)

    # weighted aggregation per action
    weighted_conf = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
    for m in models:
        w = weights.get(m, 0.0)
        for a in ("BUY", "SELL", "HOLD"):
            weighted_conf[a] += w * model_action_avg[m].get(a, 0.0)

    overall_action: Action = max(weighted_conf.items(), key=lambda x: x[1])[0]
    overall_confidence = max(weighted_conf.values()) if weighted_conf else 0.0

    vote_map = {v.model: v for v in votes}

    return ConfidenceResult(
        overall_action=overall_action if overall_confidence >= threshold else "HOLD",
        overall_confidence=overall_confidence,
        votes=vote_map,
        threshold=threshold,
    )

