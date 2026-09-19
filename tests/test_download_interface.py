from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import Mock

from src.download.entity import MarketBar
from src.download.interface import DataDownloader


class StubDownloader(DataDownloader):
    def __init__(self):
        self.fetch = Mock(return_value=[])

    def _download(self, ticker, start, end):
        return self.fetch(ticker, start, end)


class TestDataDownloader(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 9, 18, 14, 0, tzinfo=timezone.utc)
        self.end = self.start + timedelta(minutes=10)
        self.downloader = StubDownloader()

    def bar(self, timestamp):
        return MarketBar(timestamp, 2, 2.5, 1.5, 2.2, 100)

    def test_interface_requires_provider_implementation(self):
        with self.assertRaises(TypeError):
            DataDownloader()

    def test_normalized_ticker_and_valid_bars(self):
        bars = [self.bar(self.start), self.bar(self.start + timedelta(minutes=1))]
        self.downloader.fetch.return_value = bars
        self.assertEqual(self.downloader.download(" tnmg ", self.start, self.end), bars)
        self.downloader.fetch.assert_called_once_with("TNMG", self.start, self.end)

    def test_invalid_request_does_not_call_provider(self):
        for ticker, start, end in [
            ("", self.start, self.end), (None, self.start, self.end),
            ("TNMG", self.start.replace(tzinfo=None), self.end),
            ("TNMG", self.start, None), ("TNMG", self.end, self.start),
            ("TNMG", self.start, self.start),
        ]:
            with self.subTest(ticker=ticker, start=start, end=end):
                with self.assertRaises(ValueError):
                    self.downloader.download(ticker, start, end)
        self.downloader.fetch.assert_not_called()

    def test_invalid_provider_results_are_rejected(self):
        for result in [
            None, (), [{}], [self.bar(self.start - timedelta(minutes=1))],
            [self.bar(self.end)], [self.bar(self.start), self.bar(self.start)],
            [self.bar(self.start + timedelta(minutes=1)), self.bar(self.start)],
        ]:
            with self.subTest(result=result), self.assertRaises(ValueError):
                self.downloader.fetch.return_value = result
                self.downloader.download("TNMG", self.start, self.end)

    def test_different_timezones_are_compared_as_instants(self):
        shifted = self.start.astimezone(timezone(timedelta(hours=-4)))
        bars = [self.bar(shifted)]
        self.downloader.fetch.return_value = bars
        self.assertEqual(self.downloader.download("TNMG", self.start, self.end), bars)

    def test_no_bars_is_distinct_from_provider_failure(self):
        self.assertEqual(self.downloader.download("TNMG", self.start, self.end), [])
        self.downloader.fetch.side_effect = ConnectionError("Proveedor no disponible")
        with self.assertRaises(ConnectionError):
            self.downloader.download("TNMG", self.start, self.end)
