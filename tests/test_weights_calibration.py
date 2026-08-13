import math

from ammis.engines.market_math.weights import OnlineWeighter
from ammis.models.calibration import IdentityCalibrator
from ammis.models.probabilities import ModelVote


def test_weighter_update_and_weights():
    w = OnlineWeighter(decay=0.5)
    votes = [ModelVote(model='m1', action='BUY', confidence=80.0), ModelVote(model='m2', action='SELL', confidence=40.0)]
    # initial weights uniform
    ws0 = w.get_weights(['m1', 'm2'])
    assert math.isclose(ws0['m1'] + ws0['m2'], 1.0)

    # simulate realized BUY -> m1 should get lower loss
    w.update_from_feedback(votes, realized_action='BUY')
    scores = {m: w.get_score(m) for m in ['m1', 'm2']}
    assert scores['m1'] <= scores['m2']


def test_identity_calibrator_transform():
    c = IdentityCalibrator()
    assert c.transform([0.1, 0.5, 0.9]) == [0.1, 0.5, 0.9]
