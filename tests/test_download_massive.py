from datetime import datetime, timedelta, timezone
import unittest

from src.download.interface import DataDownloader
from src.download.massive import MassiveDownloader


class TestMassiveDownloader(unittest.TestCase):
    def test_pending_connection_does_not_report_empty_success(self):
        start = datetime(2026, 9, 18, 14, tzinfo=timezone.utc)
        downloader = MassiveDownloader()
        self.assertIsInstance(downloader, DataDownloader)
        self.assertIs(MassiveDownloader.download, DataDownloader.download)
        with self.assertRaisesRegex(NotImplementedError, "Massive"):
            downloader.download("TNMG", start, start + timedelta(minutes=1))

    def test_common_validation_runs_before_pending_connection(self):
        start = datetime(2026, 9, 18, 14, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ValueError, "ticker"):
            MassiveDownloader().download("", start, start + timedelta(minutes=1))
