from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone
import unittest

from src.download.entity import MarketBar


class TestMarketBar(unittest.TestCase):
    def setUp(self):
        self.values = {
            "datetime": datetime(2026, 9, 18, 14, 0, tzinfo=timezone.utc),
            "open": 2.0, "high": 2.5, "low": 1.5, "close": 2.2, "volume": 100,
        }

    def test_fields_spread_absent_zero_and_positive(self):
        self.assertEqual([field.name for field in fields(MarketBar)], [
            "datetime", "open", "high", "low", "close", "volume", "spread",
        ])
        self.assertIsNone(MarketBar(**self.values).spread)
        self.assertEqual(MarketBar(**self.values, spread=0).spread, 0)
        self.assertEqual(MarketBar(**self.values, spread=0.02).spread, 0.02)

    def test_invalid_values_are_rejected(self):
        cases = {
            "datetime": [None, "18/09/2026", datetime(2026, 9, 18)],
            "open": [0, -1, float("nan"), float("inf"), True, "2"],
            "high": [float("nan"), float("inf"), 1.0],
            "low": [float("nan"), float("inf"), 3.0],
            "close": [float("nan"), float("inf"), 4.0],
            "volume": [-1, 1.5, True, None],
            "spread": [-0.1, float("nan"), float("inf"), True, "0.1"],
        }
        for name, values in cases.items():
            for value in values:
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    MarketBar(**{**self.values, name: value})

    def test_zero_volume_and_flat_bar_are_valid(self):
        bar = MarketBar(**{**self.values, "open": 2, "high": 2, "low": 2,
                           "close": 2, "volume": 0})
        self.assertEqual(bar.volume, 0)

    def test_values_cannot_change_after_validation(self):
        bar = MarketBar(**self.values)
        with self.assertRaises(FrozenInstanceError):
            bar.volume = -1
