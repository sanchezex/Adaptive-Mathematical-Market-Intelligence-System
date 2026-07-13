from dataclasses import dataclass


@dataclass
class Order:
    action: str
    symbol: str
    quantity: float


class ExecutionEngine:
    def submit(self, order: Order) -> dict:
        # Paper trading placeholder.
        return {"status": "paper_submitted", "order": order}

