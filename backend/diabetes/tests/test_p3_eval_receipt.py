from datetime import UTC, datetime

from django.test import SimpleTestCase

from diabetes.evals.receipt import Receipt, validate_receipt


class ReceiptTests(SimpleTestCase):
    def test_valid(self):
        validate_receipt(Receipt("A", datetime(2026, 1, 1, tzinfo=UTC), ("x",), "ok"))

    def test_naive_time(self):
        with self.assertRaises(ValueError):
            validate_receipt(Receipt("A", datetime(2026, 1, 1), ("x",), "ok"))

    def test_duplicate_items(self):
        with self.assertRaises(ValueError):
            validate_receipt(Receipt("A", datetime(2026, 1, 1, tzinfo=UTC), ("x", "x"), "ok"))
