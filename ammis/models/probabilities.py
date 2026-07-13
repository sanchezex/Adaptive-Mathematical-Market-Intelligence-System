from typing import Dict, Literal

from pydantic import BaseModel

Action = Literal["BUY", "SELL", "HOLD"]


class ModelVote(BaseModel):
    model: str
    action: Action
    confidence: float  # 0..100


class ConfidenceResult(BaseModel):
    overall_action: Action
    overall_confidence: float  # 0..100
    votes: Dict[str, ModelVote]
    threshold: float

