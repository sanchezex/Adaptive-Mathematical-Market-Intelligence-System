from dataclasses import dataclass


@dataclass
class RiskLimits:
    max_daily_loss: float = 100.0
    max_weekly_loss: float = 300.0


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None):
        self.limits = limits or RiskLimits()
        # simple state tracking for demo purposes
        self.current_daily_loss: float = 0.0
        self.current_weekly_loss: float = 0.0

    def approve(self, action: str, expected_loss: float = 0.0) -> bool:
        """Approve or reject an action based on simple loss limits.

        expected_loss: positive number representing potential loss from the trade.
        """
        if action not in {"BUY", "SELL", "HOLD"}:
            return False

        if (self.current_daily_loss + expected_loss) > self.limits.max_daily_loss:
            return False
        if (self.current_weekly_loss + expected_loss) > self.limits.max_weekly_loss:
            return False

        return True

    def record_loss(self, amount: float) -> None:
        """Record realized loss (positive number)."""
        self.current_daily_loss += amount
        self.current_weekly_loss += amount

    def reset_daily(self) -> None:
        self.current_daily_loss = 0.0

    def reset_weekly(self) -> None:
        self.current_weekly_loss = 0.0

