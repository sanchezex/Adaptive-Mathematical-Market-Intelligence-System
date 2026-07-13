from dataclasses import dataclass


@dataclass
class RiskLimits:
    max_daily_loss: float = 100.0
    max_weekly_loss: float = 300.0


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None):
        self.limits = limits or RiskLimits()

    def approve(self, action: str) -> bool:
        # Placeholder: approve only BUY/SELL. Real implementation will enforce exposure limits.
        return action in {"BUY", "SELL"}

