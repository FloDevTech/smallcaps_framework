"""Archivo inicial del proveedor Massive; conexión a la API pendiente de implementar."""
from __future__ import annotations

from datetime import datetime

from .entity import MarketBar
from .interface import DataDownloader


class MassiveDownloader(DataDownloader):
    """Primer proveedor previsto; conserva la validación común de DataDownloader."""

    def _download(self, ticker: str, start: datetime, end: datetime) -> list[MarketBar]:
        raise NotImplementedError("La conexión de descarga con Massive aún no está implementada.")
