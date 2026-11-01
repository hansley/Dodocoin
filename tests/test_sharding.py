import unittest
from decimal import Decimal

from dodocoin import ShardedLedger, shard_for


class FourShardTests(unittest.TestCase):
    def setUp(self):
        self.ledger = ShardedLedger()
        names = [f"user{i}" for i in range(40)]
        for name in names:
            self.ledger.create_account(name, "100")
        self.names = names

    def pair(self, same):
        for a in self.names:
            for b in self.names:
                if a != b and ((shard_for(a) == shard_for(b)) == same):
                    return a, b
        self.fail("Could not find suitable account pair")

    def test_routing_stable_and_four_shards(self):
        self.assertEqual(shard_for("alice"), shard_for("alice"))
        self.assertEqual({shard_for(n) for n in self.names}, {0, 1, 2, 3})

    def test_same_shard_transfer(self):
        a, b = self.pair(True)
        self.assertIsNone(self.ledger.transfer(a, b, "25.50"))
        self.assertEqual(self.ledger.balance(a), Decimal("74.50"))
        self.assertEqual(self.ledger.balance(b), Decimal("125.50"))
        self.assertEqual(self.ledger.total_supply(), self.ledger.initial_supply)

    def test_cross_shard_receipt_is_exactly_once(self):
        a, b = self.pair(False)
        receipt = self.ledger.transfer(a, b, "30")
        self.assertIsNotNone(receipt)
        self.assertEqual(self.ledger.balance(a), Decimal("70"))
        self.assertEqual(self.ledger.balance(b), Decimal("100"))
        self.assertEqual(self.ledger.total_supply(), self.ledger.initial_supply)
        self.assertTrue(self.ledger.process_receipt(receipt.id))
        self.assertFalse(self.ledger.process_receipt(receipt.id))
        self.assertEqual(self.ledger.balance(b), Decimal("130"))
        self.assertEqual(self.ledger.total_supply(), self.ledger.initial_supply)

    def test_invalid_transfers_leave_balances_unchanged(self):
        a, b = self.pair(False)
        for bad in ["0", "-1", "NaN", "Infinity", "0.000000001", 1.5]:
            with self.assertRaises(ValueError):
                self.ledger.transfer(a, b, bad)
        with self.assertRaises(ValueError):
            self.ledger.transfer(a, b, "200")
        with self.assertRaises(ValueError):
            self.ledger.transfer(a, a, "1")
        self.assertEqual(self.ledger.balance(a), Decimal("100"))
        self.assertEqual(self.ledger.total_supply(), self.ledger.initial_supply)

    def test_reject_duplicate_and_unknown(self):
        with self.assertRaises(ValueError):
            self.ledger.create_account(self.names[0])
        with self.assertRaises(KeyError):
            self.ledger.transfer(self.names[0], "nobody", "1")
        with self.assertRaises(KeyError):
            self.ledger.process_receipt(999)

    def test_many_transfers_preserve_supply(self):
        for i in range(20):
            self.ledger.transfer(self.names[i], self.names[i + 1], "1.25")
        self.assertEqual(self.ledger.total_supply(), self.ledger.initial_supply)
        self.ledger.process_all_receipts()
        self.assertEqual(self.ledger.total_supply(), self.ledger.initial_supply)


if __name__ == "__main__":
    unittest.main()
