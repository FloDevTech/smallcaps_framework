from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

import polars as pl

from src.download.entity import MarketBar
from src.storage.parquet_store import ParquetStore


def bar(timestamp, **overrides):
    values = {
        "datetime": timestamp,
        "open": 2.0, "high": 2.5, "low": 1.5, "close": 2.2, "volume": 100,
    }
    values.update(overrides)
    return MarketBar(**values)


class TestParquetStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = ParquetStore(self.tmp.name)
        self.start = datetime(2026, 9, 18, 14, 0, tzinfo=timezone.utc)

    def test_count_zero_when_no_file(self):
        self.assertEqual(self.store.count("TNMG"), 0)

    def test_save_creates_file_and_counts_new_bars(self):
        bars = [bar(self.start), bar(self.start + timedelta(minutes=1))]
        self.assertEqual(self.store.save("TNMG", bars), 2)
        self.assertEqual(self.store.count("TNMG"), 2)
        self.assertTrue(self.store._path("TNMG").exists())

    def test_save_does_not_duplicate_existing(self):
        self.store.save("TNMG", [bar(self.start), bar(self.start + timedelta(minutes=1))])
        again = [bar(self.start + timedelta(minutes=1)), bar(self.start + timedelta(minutes=2))]
        self.assertEqual(self.store.save("TNMG", again), 1)
        self.assertEqual(self.store.count("TNMG"), 3)

    def test_save_preserves_existing_values(self):
        self.store.save("TNMG", [bar(self.start, transactions=3)])
        self.assertEqual(self.store.save("TNMG", [bar(self.start, transactions=99)]), 0)
        frame = pl.read_parquet(self.store._path("TNMG"))
        self.assertEqual(frame.height, 1)
        self.assertEqual(frame["transactions"][0], 3)

    def test_save_empty_bars_is_noop(self):
        self.assertEqual(self.store.save("TNMG", []), 0)
        self.assertEqual(self.store.count("TNMG"), 0)

    def test_save_sorts_by_datetime(self):
        bars = [bar(self.start + timedelta(minutes=1)), bar(self.start)]
        self.store.save("TNMG", bars)
        dts = pl.read_parquet(self.store._path("TNMG"))["datetime"].to_list()
        self.assertEqual(dts, sorted(dts))

    def test_roundtrip_optional_fields(self):
        self.store.save("TNMG", [
            bar(self.start),
            bar(self.start + timedelta(minutes=1), spread=0.02, transactions=3),
        ])
        frame = pl.read_parquet(self.store._path("TNMG"))
        self.assertIsNone(frame["spread"][0])
        self.assertIsNone(frame["transactions"][0])
        self.assertEqual(frame["spread"][1], 0.02)
        self.assertEqual(frame["transactions"][1], 3)

    def test_ticker_path_is_uppercased(self):
        self.assertEqual(self.store._path("tnmg"), Path(self.tmp.name) / "TNMG.parquet")


if __name__ == "__main__":
    unittest.main()
