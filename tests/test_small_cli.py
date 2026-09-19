from contextlib import redirect_stderr
from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from src.small_cli import (
    DEFAULT_FILE, PROJECT_ROOT, check_data_dir, load_config, load_requests, main, validate_requests,
)


CLI = Path(__file__).resolve().parents[1] / "src" / "small_cli.py"


class TestSmallCli(unittest.TestCase):
    def test_example(self):
        self.assertEqual(load_requests(DEFAULT_FILE), [
            {"ticker": "TNMG", "end_day": "18/09/2026", "days": 10},
            {"ticker": "TRUG", "end_day": "18/09/2026", "days": 10},
        ])

    def test_invalid_requests(self):
        valid = {"ticker": "TNMG", "end_day": "18/09/2026", "days": 10}
        invalid = [None, {}, [], ["TNMG"], [{"ticket": "TNMG"}]]
        for key, values in {
            "ticker": [None, "", "   ", 123],
            "end_day": [None, "31/02/2026", "2026-09-18", "1/09/2026"],
            "days": [True, 0, -1, 1.5, "10"],
        }.items():
            invalid.extend([{**valid, key: value}] for value in values)
        invalid.append([{**valid, "extra": 1}])
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_requests(data)

    def test_normalization_and_leap_day(self):
        self.assertEqual(validate_requests([
            {"ticker": " trug ", "end_day": "29/02/2024", "days": 1}
        ])[0]["ticker"], "TRUG")

    def test_default_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            config.write_text(yaml.safe_dump({"data_dir": directory, "provider": "cs"}))
            result = subprocess.run(
                [sys.executable, str(CLI), "download", "--config", str(config)],
                cwd=directory, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("TNMG", result.stdout)
            self.assertIn("TRUG", result.stdout)
            self.assertIn("cs", result.stdout)
            self.assertIn("No se han descargado datos", result.stdout)
            self.assertEqual(list(Path(directory).iterdir()), [config])

    def test_file_errors_and_no_partial_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requests.yaml"
            config = Path(directory) / "config.yaml"
            config.write_text(yaml.safe_dump({"data_dir": directory, "provider": "cs"}))
            contents = [None, "{", yaml.safe_dump([
                {"ticker": "TNMG", "end_day": "18/09/2026", "days": 10},
                {"ticker": "TRUG", "end_day": "18/09/2026", "days": 0},
            ]), "!!python/object/apply:os.system ['echo unsafe']"]
            for content in contents:
                with self.subTest(content=content):
                    if content is not None:
                        path.write_text(content, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, str(CLI), "download", "--config", str(config),
                         "--tickers", str(path)], capture_output=True, text=True,
                    )
                    self.assertEqual(result.returncode, 1)
                    self.assertIn("Error:", result.stderr)
                    self.assertEqual(result.stdout, "")
                    if content is not None:
                        self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_config_validation_and_relative_path(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            config.write_text("data_dir: data\nprovider: massive\n", encoding="utf-8")
            self.assertEqual(load_config(config), {
                "data_dir": (PROJECT_ROOT / "data").resolve(), "provider": "massive",
            })
            for provider in ("cs", "massive", "ib"):
                with self.subTest(provider=provider):
                    config.write_text(yaml.safe_dump({
                        "data_dir": directory, "provider": provider,
                    }), encoding="utf-8")
                    self.assertEqual(load_config(config)["provider"], provider)
            for data in [None, [], {}, {"data_dir": "data"},
                         {"data_dir": "", "provider": "cs"},
                         {"data_dir": 10, "provider": "cs"},
                         {"data_dir": "data", "provider": "unknown"},
                         {"data_dir": "data", "provider": "schwab"},
                         {"data_dir": "data", "provider": []}]:
                with self.subTest(data=data):
                    config.write_text(yaml.safe_dump(data), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_config(config)

    def test_destination_preserves_files_and_leaves_no_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            existing = path / "existing.txt"
            existing.write_text("keep", encoding="utf-8")
            check_data_dir(path)
            self.assertEqual(list(path.iterdir()), [existing])
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep")

    def test_destination_missing_file_and_write_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            missing = path / "missing"
            with self.assertRaisesRegex(ValueError, "no existe"):
                check_data_dir(missing)
            self.assertFalse(missing.exists())
            file = path / "file"
            file.touch()
            with self.assertRaisesRegex(ValueError, "no es un directorio"):
                check_data_dir(file)
            with patch("src.small_cli.tempfile.TemporaryFile", side_effect=PermissionError):
                with self.assertRaisesRegex(ValueError, "No se puede escribir"):
                    check_data_dir(path)

    def test_invalid_tickers_stop_before_destination_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            tickers = Path(directory) / "tickers.yaml"
            config.write_text(yaml.safe_dump({"data_dir": directory, "provider": "cs"}))
            tickers.write_text("[]", encoding="utf-8")
            with patch("src.small_cli.check_data_dir") as probe:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    result = main([
                        "download", "--config", str(config), "--tickers", str(tickers),
                    ])
                self.assertEqual(result, 1)
                probe.assert_not_called()

    def test_missing_destination_returns_error_without_success(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.yaml"
            missing = Path(directory) / "missing"
            config.write_text(yaml.safe_dump({"data_dir": str(missing), "provider": "massive"}))
            result = subprocess.run(
                [sys.executable, str(CLI), "download", "--config", str(config)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("Error:", result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertFalse(missing.exists())

    def test_only_download_command_and_help(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(CLI)], cwd=directory,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("download", result.stdout)
            for command in ["download-cs", "download-massive"]:
                result = subprocess.run([sys.executable, str(CLI), command], cwd=directory,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
