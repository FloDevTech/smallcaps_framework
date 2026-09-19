"""Catálogo de datos: registra cada descarga como una fila separada."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import polars as pl


def _atomic_write(path: Path, frame: pl.DataFrame) -> None:
    temp = path.with_name(path.name + ".tmp")
    frame.write_parquet(temp)
    temp.replace(path)


class DataCatalog:
    """Registra cada descarga como una fila independiente.

    El catálogo se guarda en {data_dir}/_catalog.parquet con columnas:
    - ticker: identificador del activo
    - start: primer datetime del rango descargado (UTC)
    - end: último datetime del rango descargado (UTC)
    - bars: cantidad de barras en esa descarga
    - updated_at: timestamp de la descarga (UTC)

    Cada descarga agrega una fila. El mismo ticker puede tener múltiples
    filas no contiguas, lo que permite ver gaps reales.
    """

    def __init__(self, data_dir: Path | str):
        self.data_dir = Path(data_dir)
        self.catalog_path = self.data_dir / "_catalog.parquet"

    def _load(self) -> pl.DataFrame:
        if not self.catalog_path.exists():
            return pl.DataFrame({
                "ticker": pl.Series([], dtype=pl.Utf8),
                "start": pl.Series([], dtype=pl.Datetime("us", "UTC")),
                "end": pl.Series([], dtype=pl.Datetime("us", "UTC")),
                "bars": pl.Series([], dtype=pl.Int64),
                "updated_at": pl.Series([], dtype=pl.Datetime("us", "UTC")),
            })
        return pl.read_parquet(self.catalog_path)

    def add(self, ticker: str, range_start: datetime, range_end: datetime, bars: int) -> None:
        """Agrega una fila de descarga al catálogo sin modificar las existentes.

        Args:
            ticker: identificador del activo (se normaliza a mayúsculas).
            range_start: primer datetime del rango descargado.
            range_end: último datetime del rango descargado.
            bars: cantidad de barras en esta descarga.
        """
        if bars == 0:
            return

        ticker = ticker.upper()
        updated_at = datetime.now(timezone.utc)

        catalog = self._load()
        new_row = pl.DataFrame({
            "ticker": [ticker],
            "start": [range_start],
            "end": [range_end],
            "bars": [bars],
            "updated_at": [updated_at],
        })
        updated = pl.concat([catalog, new_row], how="vertical_relaxed")
        updated = updated.sort("ticker", "start")
        _atomic_write(self.catalog_path, updated)

    def as_dataframe(self) -> pl.DataFrame:
        """Devuelve el catálogo completo como DataFrame para consulta."""
        return self._load()
