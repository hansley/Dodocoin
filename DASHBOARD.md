# DodoCoin dashboard

A responsive, local web interface for the four-shard simulator.

## Start

Requires **Python 3.10 or newer**. No Python packages or Node.js dependencies are needed.

From the root of the repository on the `feature/four-shard-simulator` branch:

```bash
python dashboard.py
```

Open **http://127.0.0.1:8765** on the same computer.

The simulator creates eight demonstration accounts, divided across four shards using SHA-256 routing. You can create more accounts, choose a sender and recipient, transfer test DDC and manually settle cross-shard receipts. A live activity feed shows the operations.

## Important limitations

- Everything is held **in memory** and resets on restart.
- The server binds only to localhost and is **not designed to be exposed on the internet**.
- This is a learning simulator, not a cryptocurrency or wallet: no network peers, signatures, consensus, block production, persistence, access control or real assets.
- Totals in shard cards are **display-only** JavaScript numbers; the authoritative Python ledger uses exact Decimal arithmetic.
- Cross-shard receipts must be settled manually; unprocessed balances remain in transit.
- The API is unauthenticated and is intended only for your own local computer.

## Tests

```bash
python -m unittest discover -s tests -v
```
