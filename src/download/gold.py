"""Descarga reanudable de todos los vencimientos GC accesibles con Futures Basic."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from src.download.massive_futures import GOLD_TICKER, MassiveFuturesDownloader
from src.storage.parquet_store import ParquetStore


def basic_interval(now):
    """Devuelve dos años naturales de antigüedad hasta el corte de ocho horas."""
    now = now.astimezone(timezone.utc)
    try:
        start = now.replace(year=now.year - 2)
    except ValueError:
        start = now.replace(year=now.year - 2, day=28)
    if start.second or start.microsecond:
        start = start.replace(second=0, microsecond=0) + timedelta(minutes=1)
    end = (now - timedelta(hours=8)).replace(second=0, microsecond=0)
    return start, end


def _load_progress(path):
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Checkpoint de oro no válido.")
    for ticker, entry in data.items():
        if not GOLD_TICKER.fullmatch(ticker) or not isinstance(entry, dict):
            raise ValueError("Checkpoint de oro no válido.")
        if type(entry.get("has_data")) is not bool or not isinstance(entry.get("ranges"), list):
            raise ValueError("Checkpoint de oro no válido.")
        for interval in entry["ranges"]:
            if not isinstance(interval, list) or len(interval) != 2:
                raise ValueError("Intervalo de checkpoint no válido.")
            start, end = (datetime.fromisoformat(value) for value in interval)
            if start.utcoffset() is None or end.utcoffset() is None or start >= end:
                raise ValueError("Intervalo de checkpoint no válido.")
    return data


def _missing_ranges(start, end, covered):
    cursor = start
    for left, right in sorted(
        (datetime.fromisoformat(a), datetime.fromisoformat(b)) for a, b in covered
    ):
        if right <= cursor:
            continue
        if left >= end:
            break
        if cursor < left:
            yield cursor, min(left, end)
        cursor = max(cursor, right)
    if cursor < end:
        yield cursor, end


def download_gold(data_dir, now=None, downloader=None):
    """Guarda paquetes y confirma solo aquellos completados sin errores."""
    now = now if now is not None else datetime.now(timezone.utc)
    start, end = basic_interval(now)
    downloader = downloader if downloader is not None else MassiveFuturesDownloader()
    root = Path(data_dir)
    progress_path = root / "_oro_progress.json"
    progress = _load_progress(progress_path)
    print(f"Oro GC | barras 1m | UTC [{start.isoformat()}, {end.isoformat()})", flush=True)
    print("Pausa: 13 s por petición. No ejecutes otras descargas con la misma clave.", flush=True)
    contracts = downloader.list_gold_contracts(start, end)
    if not contracts:
        raise RuntimeError("Massive no devolvió contratos GC para el histórico solicitado.")
    root.mkdir(parents=True, exist_ok=True)
    store = ParquetStore(root)
    print(f"Contratos GC encontrados: {len(contracts)} | destino: {root}", flush=True)
    for number, contract in enumerate(contracts, 1):
        ticker = contract["ticker"]
        if not GOLD_TICKER.fullmatch(ticker):
            raise ValueError("Massive devolvió un ticker GC no válido.")
        first = contract.get("first_trade_date")
        last = contract.get("last_trade_date")
        left = start
        if first:
            left = max(start, datetime.fromisoformat(first).replace(tzinfo=timezone.utc))
        right = min(end, datetime.fromisoformat(last).replace(tzinfo=timezone.utc)
                    + timedelta(days=1)) if last else end
        entry = progress.setdefault(ticker, {"has_data": False, "ranges": []})
        if entry["has_data"] and not (root / f"{ticker}.parquet").exists():
            entry = {"has_data": False, "ranges": []}
            progress[ticker] = entry
        added = 0
        packages = 0
        for gap_start, gap_end in _missing_ranges(left, right, entry["ranges"]):
            current = gap_start
            while current < gap_end:
                package_end = min(current + timedelta(days=30), gap_end)
                print(
                    f"[{number}/{len(contracts)}] {ticker} | "
                    f"{current.isoformat()} → {package_end.isoformat()}", flush=True,
                )
                bars = downloader.download(ticker, current, package_end)
                added += store.save(ticker, bars)
                entry["has_data"] = entry["has_data"] or bool(bars)
                entry["ranges"].append([current.isoformat(), package_end.isoformat()])
                temp = progress_path.with_suffix(".json.tmp")
                temp.write_text(json.dumps(progress, indent=2), encoding="utf-8")
                temp.replace(progress_path)
                current = package_end
                packages += 1
        print(f"{ticker} | nuevas: {added} | paquetes descargados: {packages}", flush=True)
    print("Descarga de oro completada.", flush=True)
    return 0
