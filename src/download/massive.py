"""Proveedor Massive: descarga barras OHLCV de 1 minuto vía REST (Custom Bars)."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Optional
import urllib.error
import urllib.parse
import urllib.request

from .entity import MarketBar
from .interface import DataDownloader


BASE_URL = "https://api.massive.com"


class MassiveDownloader(DataDownloader):
    """Descarga agregados 1m de stocks desde la API REST de Massive (ex-Polygon)."""

    def __init__(self, api_key: Optional[str] = None, adjusted: bool = False, timeout: float = 30.0):
        self.api_key = api_key if api_key is not None else os.environ.get("MASSIVE_API_KEY")
        self.adjusted = adjusted
        self.timeout = timeout

    def _download(self, ticker: str, start: datetime, end: datetime) -> list[MarketBar]:
        if not self.api_key:
            raise RuntimeError("Falta MASSIVE_API_KEY: configúrala en el entorno para descargar.")
        url = self._build_url(ticker, start, end)
        bars = []
        while url is not None:
            payload = self._get_json(url)
            bars.extend(self._to_bars(payload.get("results", [])))
            url = payload.get("next_url")
        return bars

    def _build_url(self, ticker: str, start: datetime, end: datetime) -> str:
        from_ms = int(start.timestamp() * 1000)
        to_ms = int(end.timestamp() * 1000)
        query = urllib.parse.urlencode({
            "adjusted": "true" if self.adjusted else "false",
            "sort": "asc",
            "limit": "50000",
        })
        encoded = urllib.parse.quote(ticker)
        return f"{BASE_URL}/v2/aggs/ticker/{encoded}/range/1/minute/{from_ms}/{to_ms}?{query}"

    def _get_json(self, url: str) -> dict:
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.api_key}"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Massive devolvió HTTP {exc.code} para {url}") from exc
        except urllib.error.URLError as exc:
            raise ConnectionError(f"No se pudo conectar a Massive: {exc.reason}") from exc

    def _to_bars(self, results: list) -> list[MarketBar]:
        bars = []
        for item in results:
            vwap = item.get("vw")
            transactions = item.get("n")
            bars.append(MarketBar(
                datetime=datetime.fromtimestamp(item["t"] / 1000, tz=timezone.utc),
                open=float(item["o"]),
                high=float(item["h"]),
                low=float(item["l"]),
                close=float(item["c"]),
                volume=int(item["v"]),
                vwap=float(vwap) if vwap is not None else None,
                transactions=int(transactions) if transactions is not None else None,
            ))
        return bars
