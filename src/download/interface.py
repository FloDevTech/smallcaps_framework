"""Contrato y validaciones compartidas por todos los proveedores de descarga."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import final

from .entity import MarketBar


class DataDownloader(ABC):
    """Implementar _download; conservar download como entrada común validada."""

    @final
    def download(self, ticker: str, start: datetime, end: datetime) -> list[MarketBar]:
        """Devuelve barras 1m de un ticker en [start, end), ordenadas y sin duplicados."""
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError("ticker debe ser un texto no vacío.")
        for name, value in (("start", start), ("end", end)):
            if not isinstance(value, datetime) or value.utcoffset() is None:
                raise ValueError(f"{name} debe ser una fecha con zona horaria.")
        if start >= end:
            raise ValueError("start debe ser anterior a end.")

        bars = self._download(ticker.strip().upper(), start, end)
        if not isinstance(bars, list):
            raise ValueError("El proveedor debe devolver una lista de MarketBar.")
        previous = None
        for bar in bars:
            if not isinstance(bar, MarketBar):
                raise ValueError("El proveedor devolvió una entidad distinta de MarketBar.")
            if not start <= bar.datetime < end:
                raise ValueError("El proveedor devolvió una barra fuera del intervalo solicitado.")
            if previous is not None and bar.datetime <= previous:
                raise ValueError("Las barras deben estar ordenadas y sin timestamps repetidos.")
            previous = bar.datetime
        return bars

    @abstractmethod
    def _download(self, ticker: str, start: datetime, end: datetime) -> list[MarketBar]:
        """Cada proveedor obtiene barras, las normaliza y propaga errores de descarga."""
        raise NotImplementedError
