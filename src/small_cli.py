"""Prepara la descarga validando configuración, solicitudes y directorio de destino."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys
import tempfile

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = PROJECT_ROOT / "src" / "config" / "tickers_download.yaml"
DEFAULT_CONFIG = PROJECT_ROOT / "src" / "config" / "config.yaml"


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
    if not isinstance(config, dict) or set(config) != {"data_dir", "provider"}:
        raise ValueError("La configuración debe contener exactamente data_dir y provider.")
    data_dir = config["data_dir"]
    if not isinstance(data_dir, str) or not data_dir.strip():
        raise ValueError("data_dir debe ser una ruta de directorio no vacía.")
    provider = config["provider"]
    if not isinstance(provider, str) or provider not in ("cs", "massive", "ib"):
        raise ValueError("provider debe ser cs, massive o ib.")
    destination = Path(data_dir)
    if not destination.is_absolute():
        destination = PROJECT_ROOT / destination
    return {"data_dir": destination.resolve(), "provider": provider}


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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command")
    download = commands.add_parser("download", help="Validar solicitudes y destino de descarga.")
    download.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Configuración YAML.")
    download.add_argument("--tickers", type=Path, default=DEFAULT_FILE, help="Lista de tickers YAML.")
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        config = load_config(args.config)
        requests = load_requests(args.tickers)
        check_data_dir(config["data_dir"])
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Proveedor: {config['provider']}")
    print(f"Directorio disponible: {config['data_dir']}")
    print(f"Solicitudes válidas: {len(requests)}")
    for item in requests:
        print(f"{item['ticker']} | end_day: {item['end_day']} | days: {item['days']}")
    print("Preparación completada. La descarga del proveedor aún no está implementada.")
    print("No se han descargado datos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
