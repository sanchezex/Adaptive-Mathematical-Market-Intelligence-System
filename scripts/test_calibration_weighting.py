#!/usr/bin/env python3
from ammis.models.probabilities import ModelVote
from ammis.engines.market_math.aggregator import aggregate_votes
from ammis.engines.market_math.weights import OnlineWeighter


def main():
    votes = [
        ModelVote(model='m1', action='BUY', confidence=60.0),
        ModelVote(model='m2', action='SELL', confidence=55.0),
        ModelVote(model='m3', action='BUY', confidence=70.0),
    ]

    weighter = OnlineWeighter(decay=0.9)
    # initial aggregate (uniform weights)
    res1 = aggregate_votes(votes, threshold=50.0, weighter=weighter)
    print('Before feedback:', res1.json())

    # simulate realized outcome BUY and update weighter with feedback
    weighter.update_from_feedback(votes, realized_action='BUY')

    # now aggregate again using updated weights
    res2 = aggregate_votes(votes, threshold=50.0, weighter=weighter)
    print('After feedback:', res2.json())


if __name__ == '__main__':
    main()
