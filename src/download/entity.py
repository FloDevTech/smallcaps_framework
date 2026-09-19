"""Entidad común de una barra de mercado de un minuto."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime as DateTime
from math import isfinite
from typing import Optional


@dataclass(frozen=True)
class MarketBar:
    """datetime marca el inicio con zona; spread es ask-bid o None si no hay dato."""

    datetime: DateTime
    open: float
    high: float
    low: float
    close: float
    volume: int
    spread: Optional[float] = None

    def __post_init__(self):
        if not isinstance(self.datetime, DateTime) or self.datetime.utcoffset() is None:
            raise ValueError("datetime debe ser una fecha con zona horaria.")
        for name in ("open", "high", "low", "close", "spread"):
            value = getattr(self, name)
            if name == "spread" and value is None:
                continue
            if type(value) not in (int, float) or not isfinite(value):
                raise ValueError(f"{name} debe ser un número finito.")
            if value < 0 or (name != "spread" and value == 0):
                raise ValueError(f"{name} tiene un valor fuera de rango.")
        if not self.low <= self.open <= self.high or not self.low <= self.close <= self.high:
            raise ValueError("open y close deben estar entre low y high.")
        if type(self.volume) is not int or self.volume < 0:
            raise ValueError("volume debe ser un entero no negativo.")
