"""Deterministic workload generation and real local execution measurements."""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path
from time import perf_counter_ns

from dodocoin import ShardedLedger, shard_for

ACCOUNT_COUNT = 128
DEFAULT_SEED = 20261101

def build_workload(count=10000, cross_percent=25, seed=DEFAULT_SEED):
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 1_000_000:
        raise ValueError("count must be an integer in 1..1000000")
    if not isinstance(cross_percent, int) or isinstance(cross_percent, bool) or not 0 <= cross_percent <= 100:
        raise ValueError("cross_percent must be an integer in 0..100")
    if count * cross_percent % 100:
        raise ValueError("count * cross_percent must be divisible by 100 for an exact workload")
    rng = random.Random(seed)
    buckets = {n: [] for n in range(4)}
    for i in range(ACCOUNT_COUNT):
        name = f"bench-{i:03d}"
        buckets[shard_for(name)].append(name)
    if any(len(group) < 2 for group in buckets.values()):
        raise AssertionError("Test account routing needs two accounts per shard")
    flags = [True] * (count * cross_percent // 100)
    flags += [False] * (count - len(flags))
    rng.shuffle(flags)
    transfers = []
    for cross in flags:
        source = rng.randrange(4)
        dest = (source + rng.randrange(1, 4)) % 4 if cross else source
        sender = rng.choice(buckets[source])
        recipients = [x for x in buckets[dest] if x != sender]
        recipient = rng.choice(recipients)
        transfers.append((sender, recipient, "1", cross))
    return transfers

def percentile(values, pct):
    ordered = sorted(values)
    k = (len(ordered) - 1) * pct / 100
    low = int(k)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (k - low)

def run_benchmark(count=10000, cross_percent=25, seed=DEFAULT_SEED,
                  algorithm="sha", fault="none"):
    if algorithm != "sha" or fault != "none":
        raise ValueError("Only sharding/sha with fault=none is implemented")
    transfers = build_workload(count, cross_percent, seed)
    ledger = ShardedLedger()
    for i in range(ACCOUNT_COUNT):
        ledger.create_account(f"bench-{i:03d}", "100000")
    initial_supply = ledger.initial_supply
    latencies_ns = []
    executed = Counter()
    cross_count = 0
    # Timing covers ledger transfers plus all receipt settlement, not workload generation.
    started = perf_counter_ns()
    for sender, recipient, value, expected_cross in transfers:
        t0 = perf_counter_ns()
        receipt = ledger.transfer(sender, recipient, value)
        latencies_ns.append(perf_counter_ns() - t0)
        actual_cross = receipt is not None
        assert actual_cross == expected_cross, "Cross-shard routing mismatch"
        cross_count += int(actual_cross)
        executed[shard_for(sender)] += 1
    pending_before = len(ledger.pending)
    assert pending_before == cross_count, "Missing cross-shard receipts"
    assert ledger.total_supply() == initial_supply, "Supply changed before settlement"
    settled = ledger.process_all_receipts()
    elapsed_ns = perf_counter_ns() - started
    assert settled == cross_count, "Not every receipt was settled"
    assert not ledger.pending, "Unsettled receipts remain"
    assert ledger.total_supply() == initial_supply, "Supply was not conserved"
    assert all(balance >= 0 for shard in ledger.shards for balance in shard.values()), "Negative balance"
    expected = sum((sum(shard.values(), Decimal(0)) for shard in ledger.shards), Decimal(0))
    assert expected == initial_supply, "Final balances do not match initial supply"
    per_shard = [executed[i] for i in range(4)]
    return {
        "configuration": {"category": "sharding", "algorithm": algorithm,
                          "transactions": count, "cross_shard_percent": cross_percent,
                          "seed": seed, "fault": fault, "shards": 4,
                          "accounts": ACCOUNT_COUNT},
        "simulated_workload": {"generated_transactions": len(transfers),
                               "cross_shard_transactions": cross_count,
                               "same_shard_transactions": count - cross_count},
        "measured_local_execution": {
            "wall_seconds": elapsed_ns / 1e9,
            "completed_tps": count / (elapsed_ns / 1e9),
            "transfer_latency_p50_ms": percentile(latencies_ns, 50) / 1e6,
            "transfer_latency_p95_ms": percentile(latencies_ns, 95) / 1e6,
            "transfer_latency_p99_ms": percentile(latencies_ns, 99) / 1e6,
            "transfer_latency_mean_ms": statistics.mean(latencies_ns) / 1e6,
            "source_transactions_per_shard": per_shard,
            "source_distribution_pct": [v * 100 / count for v in per_shard],
            "receipt_settlements": settled
        },
        "correctness": {"passed": True, "supply_conserved": True,
                        "all_receipts_settled": True, "no_negative_balances": True,
                        "initial_supply": str(initial_supply),
                        "final_supply": str(ledger.total_supply())},
        "limitations": "Local single-process Python timing; no network, consensus, validators or block finality. Transfer latency excludes receipt settlement; wall time and TPS include settlement."
    }

def main():
    parser = argparse.ArgumentParser(description="DodoCoin local benchmark")
    parser.add_argument("--transactions", type=int, default=10000)
    parser.add_argument("--cross-percent", type=int, default=25)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = run_benchmark(args.transactions, args.cross_percent, args.seed)
    except (ValueError, AssertionError) as e:
        parser.error(str(e))
    data = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(data + "\n", encoding="utf-8")
    print(data)

if __name__ == "__main__":
    main()
