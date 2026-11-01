"""Educational deterministic four-shard DodoCoin ledger (not a production blockchain)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from threading import RLock
from typing import Dict, List

SHARD_COUNT = 4

def amount(value: str | int | Decimal) -> Decimal:
    """Accept exact nonnegative decimal quantities; reject floats and booleans."""
    if isinstance(value, (float, bool)):
        raise ValueError("Use a decimal string, integer, or Decimal")
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid amount") from None
    if not result.is_finite() or result <= 0:
        raise ValueError("Amount must be finite and greater than zero")
    if result.as_tuple().exponent < -8:
        raise ValueError("At most 8 decimal places are supported")
    return result

def shard_for(account_id: str) -> int:
    """Stable routing independent of Python's randomised hash()."""
    if not isinstance(account_id, str) or not account_id.strip():
        raise ValueError("Account ID must be a nonempty string")
    return int.from_bytes(sha256(account_id.encode("utf-8")).digest(), "big") % SHARD_COUNT

@dataclass(frozen=True)
class Receipt:
    id: int
    sender: str
    recipient: str
    amount: Decimal
    source_shard: int
    destination_shard: int

class ShardedLedger:
    """In-memory simulator. No signatures, consensus, persistence or networking."""

    def __init__(self) -> None:
        self.shards: List[Dict[str, Decimal]] = [dict() for _ in range(SHARD_COUNT)]
        self.pending: Dict[int, Receipt] = {}
        self.completed: set[int] = set()
        self.next_receipt_id = 1
        self.initial_supply = Decimal("0")
        self._lock = RLock()

    def create_account(self, account_id: str, initial_balance: str | int | Decimal = "0") -> int:
        index = shard_for(account_id)
        if isinstance(initial_balance, (float, bool)):
            raise ValueError("Use a decimal string, integer, or Decimal")
        try:
            balance = Decimal(initial_balance)
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Invalid initial balance") from None
        if not balance.is_finite() or balance < 0 or balance.as_tuple().exponent < -8:
            raise ValueError("Initial balance must be finite, nonnegative and at most 8 decimal places")
        with self._lock:
            if account_id in self.shards[index]:
                raise ValueError("Account already exists")
            self.shards[index][account_id] = balance
            self.initial_supply += balance
        return index

    def balance(self, account_id: str) -> Decimal:
        index = shard_for(account_id)
        with self._lock:
            if account_id not in self.shards[index]:
                raise KeyError(f"Unknown account: {account_id}")
            return self.shards[index][account_id]

    def transfer(self, sender: str, recipient: str, quantity: str | int | Decimal) -> Receipt | None:
        value = amount(quantity)
        source = shard_for(sender)
        target = shard_for(recipient)
        with self._lock:
            if sender == recipient:
                raise ValueError("Cannot transfer to self")
            if sender not in self.shards[source] or recipient not in self.shards[target]:
                raise KeyError("Sender or recipient does not exist")
            if self.shards[source][sender] < value:
                raise ValueError("Insufficient funds")
            self.shards[source][sender] -= value
            if source == target:
                self.shards[target][recipient] += value
                return None
            receipt = Receipt(self.next_receipt_id, sender, recipient, value, source, target)
            self.next_receipt_id += 1
            self.pending[receipt.id] = receipt
            return receipt

    def process_receipt(self, receipt_id: int) -> bool:
        """Credit once. Return False if the receipt was already processed."""
        with self._lock:
            if receipt_id in self.completed:
                return False
            if receipt_id not in self.pending:
                raise KeyError(f"Unknown pending receipt: {receipt_id}")
            receipt = self.pending[receipt_id]
            self.shards[receipt.destination_shard][receipt.recipient] += receipt.amount
            self.completed.add(receipt_id)
            del self.pending[receipt_id]
            return True

    def process_all_receipts(self) -> int:
        with self._lock:
            ids = list(self.pending)
            for receipt_id in ids:
                self.process_receipt(receipt_id)
            return len(ids)

    def total_supply(self) -> Decimal:
        """Include funds in flight so cross-shard transfers never change supply."""
        with self._lock:
            balances = sum((sum(shard.values(), Decimal("0")) for shard in self.shards), Decimal("0"))
            inflight = sum((r.amount for r in self.pending.values()), Decimal("0"))
            return balances + inflight

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "shards": [
                    {"id": i, "accounts": {a: str(b) for a, b in sorted(shard.items())}}
                    for i, shard in enumerate(self.shards)
                ],
                "pending_receipts": [
                    {"id": r.id, "sender": r.sender, "recipient": r.recipient,
                     "amount": str(r.amount), "source": r.source_shard,
                     "destination": r.destination_shard}
                    for r in self.pending.values()
                ],
                "total_supply": str(self.total_supply()),
            }
