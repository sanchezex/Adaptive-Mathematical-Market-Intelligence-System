from dataclasses import dataclass
from datetime import datetime
from typing import Dict
import hashlib


@dataclass
class Order:
    action: str
    symbol: str
    quantity: float


class ExecutionEngine:
    """Simple paper execution engine that simulates fills deterministically.

    The engine returns a simulated fill price derived from the symbol string
    (hash-based) so behavior is repeatable for tests.
    """

    def __init__(self):
        self.trades: Dict[int, Dict] = {}
        self._next_id = 1

    def _simulate_price(self, symbol: str) -> float:
        h = hashlib.sha256(symbol.encode()).hexdigest()
        # take a slice and convert to int to make a pseudo-price
        val = int(h[:8], 16) % 10000
        price = float(val) / 100.0 + 1.0
        return price

    def submit(self, order: Order) -> dict:
        price = self._simulate_price(order.symbol)
        filled_qty = order.quantity
        trade_id = self._next_id
        self._next_id += 1
        record = {
            "id": trade_id,
            "symbol": order.symbol,
            "action": order.action,
            "quantity": filled_qty,
            "filled_price": price,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "filled",
        }
        self.trades[trade_id] = record
        return record

    def get_trade(self, trade_id: int) -> dict | None:
        return self.trades.get(trade_id)

