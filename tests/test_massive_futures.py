"""Pruebas del proveedor de futuros sin peticiones reales."""
from __future__ import annotations

from contextlib import redirect_stderr
from datetime import date, datetime, timedelta, timezone
import io
import json
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from src.download.massive_futures import MassiveFuturesDownloader, gold_reference_dates


def response(results, next_url=None):
    handle = MagicMock()
    handle.read.return_value = json.dumps({
        "status": "OK", "results": results, "next_url": next_url,
    }).encode()
    return handle


class TestMassiveFutures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        self.end = self.start + timedelta(days=1)
        self.client = MassiveFuturesDownloader(api_key="test")
        self.sleep = patch("src.download.massive_futures.time.sleep").start()
        self.addCleanup(patch.stopall)
        self.http = patch("src.download.massive_futures.urllib.request.urlopen").start()
        self.references = patch("src.download.massive_futures.gold_reference_dates").start()
        self.references.return_value = [self.end.date()]

    def test_contracts_include_expired_and_follow_pages_without_active_filter(self):
        expired = {"ticker": "GCZ4", "product_code": "GC", "active": False}
        active = {"ticker": "GCZ5", "product_code": "GC", "active": True}
        combo = {"ticker": "GCZ4-GCZ5", "product_code": "GC", "type": "combo"}
        self.http.return_value.__enter__.side_effect = [
            response([expired, combo], "https://api.massive.com/futures/v1/contracts?cursor=x"),
            response([active]),
        ]
        contracts = self.client.list_gold_contracts(self.start, self.end)
        self.assertEqual([c["ticker"] for c in contracts], ["GCZ4", "GCZ5"])
        query = parse_qs(urlsplit(self.http.call_args_list[0].args[0].full_url).query)
        self.assertEqual(query["product_code"], ["GC"])
        self.assertNotIn("type", query)
        self.assertEqual(query.get("date"), [self.end.date().isoformat()])
        self.assertNotIn("active", query)
        self.assertIn("last_trade_date.gte", query)
        self.assertEqual(self.sleep.call_args_list, [call(13), call(13)])

    def test_historical_snapshots_recover_expired_contracts_and_sort_by_expiry(self):
        self.references.return_value = [date(2024, 10, 21), date(2026, 10, 19)]
        old = {"ticker": "GCZ4", "product_code": "GC", "date": "2024-10-21",
               "type": None, "last_trade_date": "2024-12-27"}
        later = {"ticker": "GCF7", "product_code": "GC", "date": "2024-10-21",
                 "last_trade_date": "2027-01-27"}
        recent = {**later, "date": "2026-10-19", "type": "single"}
        self.http.return_value.__enter__.side_effect = [
            response([old, later]), response([recent]),
        ]
        contracts = self.client.list_gold_contracts(self.start, self.end)
        self.assertEqual([c["ticker"] for c in contracts], ["GCZ4", "GCF7"])
        self.assertEqual(contracts[1]["date"], "2026-10-19")
        queries = [parse_qs(urlsplit(c.args[0].full_url).query)
                   for c in self.http.call_args_list]
        self.assertNotIn("type", queries[0])
        self.assertEqual(queries[1]["type"], ["single"])
        self.assertEqual(self.sleep.call_args_list, [call(13), call(13)])

    def test_reference_dates_cover_months_with_business_days_inside_window(self):
        start = datetime(2024, 10, 19, 20, tzinfo=timezone.utc)
        end = datetime(2026, 10, 19, 12, tzinfo=timezone.utc)
        references = gold_reference_dates(start, end)
        self.assertEqual(references[0], date(2024, 10, 21))
        self.assertEqual(references[-1], date(2026, 10, 19))
        self.assertEqual(len(references), len(set(references)))
        self.assertTrue(all(d.weekday() < 5 for d in references))
        self.assertTrue(all(start.date() <= d <= end.date() for d in references))
        self.assertTrue(all((b - a).days <= 33 for a, b in zip(references, references[1:])))

    def test_contract_history_is_rejected_before_requesting_next_page(self):
        self.http.return_value.__enter__.return_value = response([
            {"ticker": "GCZ5", "product_code": "GC", "type": "single",
             "date": "2024-12-01"},
        ], "https://api.massive.com/futures/v1/contracts?cursor=x")
        with self.assertRaisesRegex(RuntimeError, "fecha de referencia"):
            self.client.list_gold_contracts(self.start, self.end)
        self.assertEqual(self.http.call_count, 1)

    def test_duplicate_contract_snapshot_is_not_paginated_indefinitely(self):
        record = {"ticker": "GCZ5", "product_code": "GC", "type": "single"}
        self.http.return_value.__enter__.return_value = response(
            [record, record], "https://api.massive.com/futures/v1/contracts?cursor=x",
        )
        with self.assertRaisesRegex(RuntimeError, "repetido"):
            self.client.list_gold_contracts(self.start, self.end)
        self.assertEqual(self.http.call_count, 1)

    def test_unrelated_product_stops_discovery_instead_of_scanning_full_market(self):
        self.http.return_value.__enter__.return_value = response([
            {"ticker": "ESZ5", "product_code": "ES", "type": "single"},
        ], "https://api.massive.com/futures/v1/contracts?cursor=x")
        with self.assertRaisesRegex(RuntimeError, "producto distinto de GC"):
            self.client.list_gold_contracts(self.start, self.end)
        self.assertEqual(self.http.call_count, 1)

    def test_aggregates_use_ns_range_and_map_full_field_names(self):
        row = {
            "window_start": 1735689600000000000, "open": 2600, "high": 2602,
            "low": 2599, "close": 2601, "volume": 100, "transactions": 8,
        }
        self.http.return_value.__enter__.side_effect = [
            response([row], "https://api.massive.com/futures/v1/aggs/GCZ5?cursor=x"),
            response([{**row, "window_start": 1735689660000000000}]),
        ]
        bars = self.client.download("GCZ5", self.start, self.end)
        self.assertEqual(len(bars), 2)
        self.assertEqual(bars[0].datetime, self.start)
        self.assertEqual(bars[0].transactions, 8)
        self.assertIsNone(bars[0].spread)
        query = parse_qs(urlsplit(self.http.call_args_list[0].args[0].full_url).query)
        self.assertEqual(query["resolution"], ["1min"])
        self.assertEqual(query["window_start.gte"], ["1735689600000000000"])
        self.assertEqual(query["window_start.lt"], ["1735776000000000000"])
        self.assertEqual(self.sleep.call_args_list, [call(13), call(13)])

    def test_429_retries_after_backoff_and_is_rate_limited(self):
        success = MagicMock()
        success.__enter__.return_value = response([])
        self.http.side_effect = [
            HTTPError("https://api.massive.com", 429, "rate", {"Retry-After": "90"}, None),
            success,
        ]
        self.assertEqual(self.client.list_gold_contracts(self.start, self.end), [])
        self.assertEqual(self.sleep.call_args_list, [call(13), call(90), call(13)])

    def test_429_exhaustion_is_error(self):
        self.http.side_effect = HTTPError("https://api.massive.com", 429, "rate", {}, None)
        with self.assertRaisesRegex(RuntimeError, "429"):
            self.client.list_gold_contracts(self.start, self.end)
        self.assertEqual(self.http.call_count, 4)

    def test_access_error_explains_futures_entitlement(self):
        self.http.side_effect = HTTPError("https://api.massive.com", 403, "no", {}, None)
        with self.assertRaisesRegex(RuntimeError, "Futures"):
            self.client.list_gold_contracts(self.start, self.end)
        self.assertEqual(self.http.call_count, 1)

    def test_missing_key_does_not_call_http(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "MASSIVE_API_KEY"):
                MassiveFuturesDownloader().list_gold_contracts(self.start, self.end)
        self.http.assert_not_called()

    def test_error_payload_and_foreign_pagination_are_rejected(self):
        broken = MagicMock()
        broken.read.return_value = b'{"status":"ERROR","error":"no"}'
        self.http.return_value.__enter__.return_value = broken
        with self.assertRaisesRegex(RuntimeError, "respuesta"):
            self.client.list_gold_contracts(self.start, self.end)
        self.http.return_value.__enter__.return_value = response([], "https://example.com/x")
        with self.assertRaisesRegex(ValueError, "paginaci"):
            self.client.list_gold_contracts(self.start, self.end)

    def test_repeated_page_is_an_error(self):
        self.http.return_value.__enter__.return_value = response(
            [], "https://api.massive.com/futures/v1/contracts?cursor=x",
        )
        with self.assertRaisesRegex(ValueError, "Paginación"):
            self.client.list_gold_contracts(self.start, self.end)
        self.assertEqual(self.http.call_count, 2)

    def test_out_of_range_bar_is_rejected_by_shared_contract(self):
        row = {
            "window_start": 1735776000000000000, "open": 2600, "high": 2602,
            "low": 2599, "close": 2601, "volume": 100,
        }
        self.http.return_value.__enter__.return_value = response([row])
        with self.assertRaisesRegex(ValueError, "fuera del intervalo"):
            self.client.download("GCZ5", self.start, self.end)

    def test_progress_exposes_waits_and_pages_without_credentials(self):
        success = MagicMock()
        success.__enter__.return_value = response(
            [], "https://api.massive.com/futures/v1/contracts?cursor=private-cursor",
        )
        last_page = MagicMock()
        last_page.__enter__.return_value = response([])
        self.http.side_effect = [
            HTTPError("https://api.massive.com", 429, "rate", {"Retry-After": "90"}, None),
            success, last_page,
        ]
        self.client.api_key = "secret-api-key"
        with redirect_stderr(io.StringIO()) as output:
            self.client.list_gold_contracts(self.start, self.end)
        messages = output.getvalue()
        for expected in ("pausa 13 s", "Conectando", "HTTP 429", "90 s", "Página 2"):
            self.assertIn(expected, messages)
        self.assertNotIn("secret-api-key", messages)
        self.assertNotIn("private-cursor", messages)


if __name__ == "__main__":
    unittest.main()
