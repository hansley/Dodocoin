"""Run: python demo.py"""
import json
from dodocoin import ShardedLedger, shard_for

ledger = ShardedLedger()
accounts = ["alice", "bob", "charlie", "diana", "eve", "frank", "grace", "heidi"]
for name in accounts:
    shard = ledger.create_account(name, "100")
    print(f"{name:8s} -> shard {shard}")

alice = "alice"
receiver = next(a for a in accounts if shard_for(a) != shard_for(alice))
print(f"\nSending 30 DDC from {alice} to {receiver}")
receipt = ledger.transfer(alice, receiver, "30")
print("Cross-shard receipt queued:", receipt)
print("Supply before receipt settlement:", ledger.total_supply())
ledger.process_all_receipts()
print("Balance alice:", ledger.balance(alice))
print(f"Balance {receiver}:", ledger.balance(receiver))
print("Supply after receipt settlement:", ledger.total_supply())
print(json.dumps(ledger.snapshot(), indent=2))
