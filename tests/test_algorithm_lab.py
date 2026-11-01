"""Correctness and determinism tests for algorithm lab."""
import unittest
from algorithm_lab import build_workload, run_benchmark
from dodocoin import shard_for

class AlgorithmLabTests(unittest.TestCase):
    def test_same_seed_exact_workload(self):
        first = build_workload(1000, 25, 42)
        self.assertEqual(first, build_workload(1000, 25, 42))
        self.assertNotEqual(first, build_workload(1000, 25, 43))
        self.assertEqual(sum(t[3] for t in first), 250)
        self.assertTrue(all((shard_for(a) != shard_for(b)) == cross for a, b, _, cross in first))

    def test_real_ledger_invariants(self):
        result = run_benchmark(1000, 25, 42)
        self.assertEqual(result["simulated_workload"]["cross_shard_transactions"], 250)
        self.assertEqual(result["measured_local_execution"]["receipt_settlements"], 250)
        self.assertEqual(sum(result["measured_local_execution"]["source_transactions_per_shard"]), 1000)
        self.assertTrue(all(result["correctness"][k] for k in
                            ("passed", "supply_conserved", "all_receipts_settled", "no_negative_balances")))
        self.assertGreater(result["measured_local_execution"]["completed_tps"], 0)

    def test_zero_and_full_cross_shard(self):
        for fraction in (0, 100):
            result = run_benchmark(100, fraction, 11)
            self.assertEqual(result["simulated_workload"]["cross_shard_transactions"], fraction)
            self.assertTrue(result["correctness"]["passed"])

    def test_invalid_parameters(self):
        for count, ratio in [(0,25), (101,25), (10,-1), (10,101)]:
            with self.assertRaises(ValueError):
                run_benchmark(count, ratio)
        with self.assertRaises(ValueError):
            run_benchmark(100, 25, algorithm="unimplemented")
        with self.assertRaises(ValueError):
            run_benchmark(100, 25, fault="partition")

if __name__ == "__main__":
    unittest.main()
