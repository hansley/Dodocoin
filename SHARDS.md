# DodoCoin four-shard simulator

This is a **single-process, in-memory educational simulator**, not a cryptocurrency network. It does not provide signed transactions, block consensus, persistent storage, Merkle trees, networking, authentication, or real-fund security.

## Run

Requires Python 3.10+ and no third-party packages.

```bash
python demo.py
python -m unittest discover -s tests -v
```

## How it works

- Exactly **four shards** indexed 0–3.
- Account IDs map to shards using SHA-256 modulo four (not alphabetically).
- Balances use exact decimal arithmetic (up to eight decimal places).
- Accounts begin with simulated balances specified by the caller; no token minting policy exists.
- Same-shard transfers debit and credit synchronously.
- Cross-shard transfers debit the sender and create a pending receipt. Calling `process_receipt(id)` or `process_all_receipts()` credits the destination.
- Pending value is counted as **in flight** when checking conservation of supply.
- Replaying a completed receipt does not credit twice.
- A process restart loses the ledger: persistence and crash recovery have not been implemented.
- A global in-process lock serialises operations. It is not distributed consensus.

## Next steps

Add signed transactions and nonces, persistent journalling and recovery, deterministic chunk/block commitments, networked nodes, validators, and adversarial tests **before** any production use.
