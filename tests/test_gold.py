"""Pruebas de persistencia y reanudación del comando oro."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import polars as pl

from src.download.entity import MarketBar
from src.download.gold import basic_interval, download_gold
from src.small_cli import main


class TestGold(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = datetime(2026, 10, 19, 17, 18, 30, tzinfo=timezone.utc)
        self.start, self.end = basic_interval(self.now)
        self.client = MagicMock()
        self.client.list_gold_contracts.return_value = [{
            "ticker": "GCZ6", "first_trade_date": "2026-10-01",
            "last_trade_date": "2026-12-29",
        }]

    def run_gold(self):
        with redirect_stdout(io.StringIO()):
            return download_gold(self.root, now=self.now, downloader=self.client)

    def test_basic_interval_has_two_years_and_eight_hour_cutoff(self):
        self.assertEqual(self.start, datetime(2024, 10, 19, 17, 19, tzinfo=timezone.utc))
        self.assertEqual(self.end, datetime(2026, 10, 19, 9, 18, tzinfo=timezone.utc))
        leap_start, _ = basic_interval(datetime(2024, 2, 29, tzinfo=timezone.utc))
        self.assertEqual(leap_start.date().isoformat(), "2022-02-28")

    def test_persists_separately_and_resumes_even_empty_intervals(self):
        first = datetime(2026, 10, 1, tzinfo=timezone.utc)
        bar = MarketBar(first, 2600, 2602, 2599, 2601, 10)
        self.client.download.return_value = [bar]
        self.run_gold()
        path = self.root / "GCZ6.parquet"
        self.assertEqual(pl.read_parquet(path).height, 1)
        self.client.download.reset_mock()
        self.run_gold()
        self.client.download.assert_not_called()
        self.assertEqual(pl.read_parquet(path).height, 1)
        self.client.list_gold_contracts.return_value.append({"ticker": "GCZ7"})
        self.client.download.return_value = []
        self.run_gold()
        self.client.download.reset_mock()
        self.run_gold()
        self.client.download.assert_not_called()

    def test_failed_package_is_retried_without_repeating_successful_package(self):
        self.client.list_gold_contracts.return_value = [{"ticker": "GCZ6"}]
        self.client.download.side_effect = [[], RuntimeError("fallo")]
        with self.assertRaisesRegex(RuntimeError, "fallo"):
            self.run_gold()
        first_call, failed_call = self.client.download.call_args_list
        self.assertLess(first_call.args[1], first_call.args[2])
        self.client.download.reset_mock()
        self.client.download.side_effect = None
        self.client.download.return_value = []
        self.run_gold()
        self.assertEqual(self.client.download.call_args_list[0], failed_call)
        self.assertNotIn(first_call, self.client.download.call_args_list)

    def test_missing_data_file_invalidates_nonempty_checkpoint(self):
        first = datetime(2026, 10, 1, tzinfo=timezone.utc)
        self.client.download.return_value = [MarketBar(first, 1, 1, 1, 1, 1)]
        self.run_gold()
        (self.root / "GCZ6.parquet").unlink()
        self.client.download.reset_mock()
        self.run_gold()
        self.client.download.assert_called_once()

    def test_corrupt_checkpoint_is_error(self):
        (self.root / "_oro_progress.json").write_text("{} broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_gold()
        self.client.download.assert_not_called()

    def test_new_cutoff_downloads_only_new_tail(self):
        self.client.download.return_value = []
        self.run_gold()
        self.client.download.reset_mock()
        with redirect_stdout(io.StringIO()):
            download_gold(self.root, now=self.now + timedelta(days=1), downloader=self.client)
        self.client.download.assert_called_once_with(
            "GCZ6", self.end, self.end + timedelta(days=1),
        )

    def test_storage_failure_does_not_confirm_interval(self):
        self.client.download.return_value = []
        with patch("src.download.gold.ParquetStore.save", side_effect=OSError("disco")):
            with self.assertRaisesRegex(OSError, "disco"):
                self.run_gold()
        self.assertFalse((self.root / "_oro_progress.json").exists())

    def test_empty_discovery_is_an_error_without_success(self):
        self.client.list_gold_contracts.return_value = []
        with self.assertRaisesRegex(RuntimeError, "no devolvió contratos"):
            self.run_gold()
        self.assertFalse((self.root / "_oro_progress.json").exists())

    def test_cli_oro_does_not_load_stock_requests_or_use_stock_downloader(self):
        with patch("src.small_cli.load_config", return_value={"data_dir": self.root}), \
                patch("src.small_cli.load_requests") as stock_requests, \
                patch("src.small_cli.download_massive") as stocks, \
                patch("src.small_cli.download_gold") as gold:
            gold.return_value = 0
            self.assertEqual(main(["oro"]), 0)
            gold.assert_called_once_with(self.root / "oro")
            stock_requests.assert_not_called()
            stocks.assert_not_called()

    def test_cli_explicit_root_does_not_require_stock_config_and_reports_error(self):
        with patch("src.small_cli.load_config") as config, \
                patch("src.small_cli.download_gold", side_effect=RuntimeError("HTTP 403")), \
                redirect_stderr(io.StringIO()) as output:
            self.assertEqual(main(["oro", "--data-dir", str(self.root)]), 1)
            self.assertIn("HTTP 403", output.getvalue())
            config.assert_not_called()


if __name__ == "__main__":
    unittest.main()
