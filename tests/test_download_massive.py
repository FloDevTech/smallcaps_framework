import json
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from src.download.entity import MarketBar
from src.download.interface import DataDownloader
from src.download.massive import MassiveDownloader


def _bar(timestamp, o=2.0, h=2.5, l=1.5, c=2.2, v=100, vw=2.1, n=3):
    payload = {"t": timestamp, "o": o, "h": h, "l": l, "c": c, "v": v}
    if vw is not None:
        payload["vw"] = vw
    if n is not None:
        payload["n"] = n
    return payload


def _json_response(payload):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    return response


class TestMassiveDownloader(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 9, 18, 14, 0, tzinfo=timezone.utc)
        self.downloader = MassiveDownloader(api_key="test-key")

    def _ts(self, offset_minutes=0):
        return int((self.start + timedelta(minutes=offset_minutes)).timestamp() * 1000)

    def test_is_a_data_downloader(self):
        self.assertIsInstance(self.downloader, DataDownloader)
        self.assertIs(MassiveDownloader.download, DataDownloader.download)

    def test_common_validation_runs_before_connection(self):
        with self.assertRaisesRegex(ValueError, "ticker"):
            self.downloader.download("", self.start, self.start + timedelta(minutes=1))

    def test_missing_api_key_raises(self):
        downloader = MassiveDownloader(api_key=None)
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "MASSIVE_API_KEY"):
                downloader.download("TNMG", self.start, self.start + timedelta(minutes=1))

    def test_maps_bars_including_vwap_and_transactions(self):
        payload = {"results": [_bar(self._ts(0))], "next_url": None}
        with patch("src.download.massive.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = _json_response(payload)
            bars = self.downloader.download("TNMG", self.start, self.start + timedelta(minutes=2))
        self.assertEqual(len(bars), 1)
        bar = bars[0]
        self.assertIsInstance(bar, MarketBar)
        self.assertEqual(bar.vwap, 2.1)
        self.assertEqual(bar.transactions, 3)
        self.assertIsNone(bar.spread)

    def test_absent_vwap_and_transactions_become_none(self):
        payload = {"results": [_bar(self._ts(0), vw=None, n=None)], "next_url": None}
        with patch("src.download.massive.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value = _json_response(payload)
            bars = self.downloader.download("TNMG", self.start, self.start + timedelta(minutes=2))
        self.assertIsNone(bars[0].vwap)
        self.assertIsNone(bars[0].transactions)

    def test_pagination_follows_next_url(self):
        page1 = {"results": [_bar(self._ts(0))], "next_url": "https://api.massive.com/next?cursor=x"}
        page2 = {"results": [_bar(self._ts(1))], "next_url": None}
        with patch("src.download.massive.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.side_effect = [
                _json_response(page1), _json_response(page2),
            ]
            bars = self.downloader.download("TNMG", self.start, self.start + timedelta(minutes=3))
        self.assertEqual(len(bars), 2)

    def test_http_error_propagates(self):
        with patch(
            "src.download.massive.urllib.request.urlopen",
            side_effect=HTTPError("http://api.massive.com", 429, "Too Many Requests", {}, None),
        ):
            with self.assertRaisesRegex(RuntimeError, "HTTP 429"):
                self.downloader.download("TNMG", self.start, self.start + timedelta(minutes=1))

    def test_url_uses_ms_timestamps_and_params(self):
        url = self.downloader._build_url("TNMG", self.start, self.start + timedelta(minutes=1))
        self.assertIn("/v2/aggs/ticker/TNMG/range/1/minute/", url)
        self.assertIn("adjusted=false", url)
        self.assertIn("sort=asc", url)
        self.assertIn("limit=50000", url)


if __name__ == "__main__":
    unittest.main()
