"""Descarga barras 1m de los tickers solicitados, de forma incremental en Parquet."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile

import logging
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.download.massive import MassiveDownloader
from src.logger import setup_logger
from src.storage.catalog import DataCatalog
from src.storage.parquet_store import ParquetStore

DEFAULT_FILE = PROJECT_ROOT / "src" / "config" / "tickers_download.yaml"
DEFAULT_CONFIG = PROJECT_ROOT / "src" / "config" / "config.yaml"

logger = logging.getLogger("smallcaps")


def validate_requests(data):
    if not isinstance(data, list) or not data:
        raise ValueError("El YAML debe contener una lista no vacía de solicitudes.")

    requests = []
    for number, item in enumerate(data, start=1):
        prefix = f"Solicitud {number}"
        if not isinstance(item, dict) or set(item) != {"ticker", "end_day", "days"}:
            raise ValueError(f"{prefix}: usa exactamente ticker, end_day y days.")

        ticker = item["ticker"]
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError(f"{prefix}: ticker debe ser un texto no vacío.")

        end_day = item["end_day"]
        try:
            date = datetime.strptime(end_day, "%d/%m/%Y")
            if date.strftime("%d/%m/%Y") != end_day:
                raise ValueError
        except (TypeError, ValueError):
            message = f"{prefix}: end_day debe ser una fecha válida DD/MM/AAAA."
            raise ValueError(message) from None

        days = item["days"]
        if type(days) is not int or days <= 0:
            raise ValueError(f"{prefix}: days debe ser un entero positivo.")
        requests.append({"ticker": ticker.strip().upper(), "end_day": end_day, "days": days})
    return requests


def load_yaml(path):
    with Path(path).open(encoding="utf-8-sig") as source:
        return yaml.safe_load(source)


def load_requests(path):
    return validate_requests(load_yaml(path))


def load_config(path):
    config = load_yaml(path)
    if not isinstance(config, dict) or set(config) != {"data_dir", "dir_log", "provider", "package_days", "request_delay"}:
        raise ValueError("La configuración debe contener exactamente data_dir, dir_log, provider, package_days y request_delay.")
    data_dir = config["data_dir"]
    if not isinstance(data_dir, str) or not data_dir.strip():
        raise ValueError("data_dir debe ser una ruta de directorio no vacía.")
    dir_log = config["dir_log"]
    if not isinstance(dir_log, str) or not dir_log.strip():
        raise ValueError("dir_log debe ser una ruta de directorio no vacía.")
    provider = config["provider"]
    if not isinstance(provider, str) or provider not in ("cs", "massive", "ib"):
        raise ValueError("provider debe ser cs, massive o ib.")
    package_days = config["package_days"]
    if type(package_days) is not int or package_days <= 0:
        raise ValueError("package_days debe ser un entero positivo.")
    request_delay = config["request_delay"]
    if not isinstance(request_delay, (int, float)) or isinstance(request_delay, bool) or request_delay < 0:
        raise ValueError("request_delay debe ser un número mayor o igual a 0.")
    destination = Path(data_dir)
    if not destination.is_absolute():
        destination = PROJECT_ROOT / destination
    log_destination = Path(dir_log)
    if not log_destination.is_absolute():
        log_destination = PROJECT_ROOT / log_destination
    return {
        "data_dir": destination.resolve(),
        "dir_log": log_destination.resolve(),
        "provider": provider,
        "package_days": package_days,
        "request_delay": float(request_delay),
    }


def check_data_dir(path):
    if not path.exists():
        raise ValueError(f"El directorio de datos no existe: {path}")
    if not path.is_dir():
        raise ValueError(f"La ruta de datos no es un directorio: {path}")
    try:
        with tempfile.TemporaryFile(dir=path, prefix=".small_cli_check_") as probe:
            probe.write(b"check")
            probe.flush()
    except OSError as exc:
        message = f"No se puede escribir en el directorio de datos {path}: {exc}"
        raise ValueError(message) from exc


def to_interval(end_day, days):
    """Convierte end_day (DD/MM/AAAA) y days en [start, end) en UTC, con end_day inclusive."""
    date = datetime.strptime(end_day, "%d/%m/%Y")
    end = datetime(date.year, date.month, date.day, tzinfo=timezone.utc) + timedelta(days=1)
    start = end - timedelta(days=days)
    return start, end


def iter_packages(start, end, package_days):
    """Divide [start, end) en sub-rangos de a lo sumo package_days días."""
    step = timedelta(days=package_days)
    current = start
    while current < end:
        next_end = min(current + step, end)
        yield current, next_end
        current = next_end


def download_massive(config, requests):
    """Descarga cada ticker en paquetes de package_days días, de forma incremental."""
    downloader = MassiveDownloader(request_delay=config["request_delay"])
    store = ParquetStore(config["data_dir"])
    package_days = config["package_days"]
    for item in requests:
        ticker = item["ticker"]
        start, end = to_interval(item["end_day"], item["days"])
        before = store.count(ticker)
        try:
            added = 0
            for package_start, package_end in iter_packages(start, end, package_days):
                bars = downloader.download(ticker, package_start, package_end)
                added += store.save(ticker, bars)
        except Exception as exc:  # el CLI reporta el error y no crashea
            logger.error(f"Error descargando {ticker}: {exc}")
            return 1
        logger.info(f"{ticker} | antes: {before} | nuevas: {added} | total: {before + added}")
    logger.info("Descarga completada.")
    return 0


def show_catalog(data_dir):
    """Muestra el catálogo de tickers y períodos disponibles."""
    catalog = DataCatalog(data_dir)
    df = catalog.as_dataframe()
    if df.height == 0:
        print("Catálogo vacío. No hay datos registrados.")
        return 0
    print(df)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")
    download = commands.add_parser("download", help="Descargar barras 1m de los tickers solicitados.")
    download.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Configuración YAML.")
    download.add_argument("--tickers", type=Path, default=DEFAULT_FILE, help="Lista de tickers YAML.")

    catalog_cmd = commands.add_parser("catalog", help="Mostrar el catálogo de datos disponibles.")
    catalog_cmd.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Configuración YAML.")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "catalog":
        try:
            config = load_config(args.config)
            check_data_dir(config["data_dir"])
        except (OSError, ValueError, yaml.YAMLError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return show_catalog(config["data_dir"])

    try:
        config = load_config(args.config)
        requests = load_requests(args.tickers)
        check_data_dir(config["data_dir"])
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    setup_logger(config["dir_log"])

    logger.info(f"Proveedor: {config['provider']}")
    logger.info(f"Directorio de datos: {config['data_dir']}")
    logger.info(f"Solicitudes válidas: {len(requests)}")

    if config["provider"] != "massive":
        for item in requests:
            logger.info(f"{item['ticker']} | end_day: {item['end_day']} | days: {item['days']}")
        logger.warning(f"El proveedor {config['provider']} aún no está implementado.")
        logger.info("No se han descargado datos.")
        return 0

    return download_massive(config, requests)


if __name__ == "__main__":
    sys.exit(main())
