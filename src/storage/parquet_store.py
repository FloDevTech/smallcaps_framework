"""Almacenamiento de barras 1m en Parquet, un archivo por ticker."""
from __future__ import annotations

from pathlib import Path

import polars as pl

from src.download.entity import MarketBar


def _bars_to_frame(bars: list[MarketBar]) -> pl.DataFrame:
    return pl.DataFrame({
        "datetime": pl.Series([bar.datetime for bar in bars], dtype=pl.Datetime("us", "UTC")),
        "open": pl.Series([bar.open for bar in bars], dtype=pl.Float64),
        "high": pl.Series([bar.high for bar in bars], dtype=pl.Float64),
        "low": pl.Series([bar.low for bar in bars], dtype=pl.Float64),
        "close": pl.Series([bar.close for bar in bars], dtype=pl.Float64),
        "volume": pl.Series([bar.volume for bar in bars], dtype=pl.Int64),
        "spread": pl.Series([bar.spread for bar in bars], dtype=pl.Float64),
        "vwap": pl.Series([bar.vwap for bar in bars], dtype=pl.Float64),
        "transactions": pl.Series([bar.transactions for bar in bars], dtype=pl.Int64),
    })


def _atomic_write(path: Path, frame: pl.DataFrame) -> None:
    temp = path.with_name(path.name + ".tmp")
    frame.write_parquet(temp)
    temp.replace(path)


class ParquetStore:
    """Guarda barras en {data_dir}/{TICKER}.parquet conservando lo existente y sin duplicar."""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)

    def _path(self, ticker: str) -> Path:
        return self.data_dir / f"{ticker.upper()}.parquet"

    def count(self, ticker: str) -> int:
        path = self._path(ticker)
        if not path.exists():
            return 0
        return pl.read_parquet(path).height

    def save(self, ticker: str, bars: list[MarketBar]) -> int:
        """Conserva las barras existentes y devuelve cuántas barras nuevas agregó."""
        if not bars:
            return 0
        path = self._path(ticker)
        new_frame = _bars_to_frame(bars)
        if path.exists():
            existing = pl.read_parquet(path)
            before = existing.height
            combined = pl.concat([existing, new_frame], how="vertical_relaxed")
            combined = combined.unique(subset=["datetime"], keep="first")
        else:
            before = 0
            combined = new_frame.unique(subset=["datetime"], keep="first")
        combined = combined.sort("datetime")
        _atomic_write(path, combined)
        return combined.height - before
