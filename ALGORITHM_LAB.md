# DodoCoin Algorithm Lab (SHA baseline)

The lab runs a **real local Python benchmark**, not sample or fabricated performance figures.

## Dashboard

```bash
python dashboard.py
```

Open http://127.0.0.1:8765 and select **Run actual benchmark** under **Algorithm Lab**.
The dashboard initially says "Not run yet" and displays measured results only after the Python benchmark completes. It stores the most recent result in server memory until restart. Benchmark funds are separate from interactive dashboard accounts.

## Command line

```bash
python algorithm_lab.py --transactions 10000 --cross-percent 25 --seed 20261101 --output results.json
python -m unittest discover -s tests -v
```

Python 3.10+; standard library only.

## Reproducibility

- `random.Random(seed)` creates a deterministic sequence of account pairs and cross-shard flags.
- Four buckets are assigned by SHA-256 modulo four over 128 accounts.
- Workload always has exactly 7,500 same-shard and 2,500 cross-shard transactions for the requested configuration.
- Each account starts with 100,000 **simulated** DDC, and each transfer sends 1 test DDC to avoid failure from insufficient funds.
- Each cross-shard debit queues a receipt; receipts are all settled after transfers.
- Correctness asserts exact total-supply conservation before and after settlement, all receipts processed, no negative balances and exact cross-shard count.

## Real measurements vs simulation

**Simulated workload inputs:** number of transactions, shard allocation, seeded account pairs, cross-shard ratio and fault scenario (none). No network or validators are simulated in this baseline.

**Measured locally using `time.perf_counter_ns()`:** wall-clock execution duration, transfers/sec including receipt settlement, transfer execution latencies (P50/P95/P99), source transactions per shard and number of receipt settlements. Workload generation and account initialisation are excluded from timing. Individual transfer latency excludes the later receipt settlement. Reported throughput is **not** distributed-network TPS or blockchain finality.

The reproducible **transaction sequence** is identical between runs with the same seed, but measured timings are not deterministic: they vary by CPU, interpreter and machine load. Benchmark Python's single-process ledger, not a distributed blockchain. No result is claimed until run locally.

## Implementation scope

Only `category=sharding`, `algorithm=sha`, `fault=none` is implemented. Other algorithms or failures are rejected, rather than returning invented metrics.
