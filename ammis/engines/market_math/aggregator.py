from typing import Dict, List

from ammis.models.probabilities import Action, ConfidenceResult, ModelVote


def aggregate_votes(votes: List[ModelVote], threshold: float = 80.0) -> ConfidenceResult:
    # Placeholder aggregator: average confidence per action.
    by_action: Dict[Action, List[ModelVote]] = {"BUY": [], "SELL": [], "HOLD": []}
    for v in votes:
        by_action[v.action].append(v)

    def avg_conf(action: Action) -> float:
        lst = by_action[action]
        return sum(x.confidence for x in lst) / len(lst) if lst else 0.0

    buy_c = avg_conf("BUY")
    sell_c = avg_conf("SELL")
    hold_c = avg_conf("HOLD")

    overall_action: Action = max([("BUY", buy_c), ("SELL", sell_c), ("HOLD", hold_c)], key=lambda x: x[1])[0]
    overall_confidence = max(buy_c, sell_c, hold_c)

    vote_map = {v.model: v for v in votes}

    return ConfidenceResult(
        overall_action=overall_action if overall_confidence >= threshold else "HOLD",
        overall_confidence=overall_confidence,
        votes=vote_map,
        threshold=threshold,
    )

