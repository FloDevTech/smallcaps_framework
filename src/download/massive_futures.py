"""Proveedor independiente de futuros Massive Basic con cinco peticiones por minuto."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from src.download.entity import MarketBar
from src.download.interface import DataDownloader


BASE_URL = "https://api.massive.com"
REQUEST_DELAY = 13
MAX_RETRIES = 3
GOLD_TICKER = re.compile(r"GC[FGHJKMNQUVXZ][0-9]{1,4}")
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def timestamp_ns(value: datetime) -> int:
    delta = value - EPOCH
    return ((delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds) * 1000


def gold_reference_dates(start, end):
    """Fechas mensuales para descubrir GC que ya no figura en el catálogo actual."""
    first = start.astimezone(timezone.utc).date()
    last = end.astimezone(timezone.utc).date()
    dates = set()
    current = first
    while current <= last:
        business_day = current
        while business_day.weekday() >= 5:
            business_day += timedelta(days=1)
        if business_day <= last:
            dates.add(business_day)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    while last.weekday() >= 5:
        last -= timedelta(days=1)
    if last >= first:
        dates.add(last)
    return sorted(dates)


class MassiveFuturesDownloader(DataDownloader):
    """Descubre GC y descarga barras 1m sin usar el conector de acciones."""

    def __init__(self, api_key=None, timeout=30):
        self.api_key = api_key if api_key is not None else os.environ.get("MASSIVE_API_KEY")
        self.timeout = timeout

    def _get_json(self, url):
        if not self.api_key:
            raise RuntimeError("Falta MASSIVE_API_KEY en el entorno.")
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "api.massive.com":
            raise ValueError("URL de paginación de Massive no válida.")
        request = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {self.api_key}"},
        )
        for attempt in range(MAX_RETRIES + 1):
            print(
                f"Massive {parsed.path} | intento {attempt + 1}/{MAX_RETRIES + 1} "
                f"| pausa {REQUEST_DELAY} s", file=sys.stderr, flush=True,
            )
            time.sleep(REQUEST_DELAY)
            print(
                f"Conectando a Massive (timeout de red: {self.timeout} s)...",
                file=sys.stderr, flush=True,
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt < MAX_RETRIES:
                    retry_after = exc.headers.get("Retry-After", "60")
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        try:
                            date = parsedate_to_datetime(retry_after)
                            delay = (date - datetime.now(timezone.utc)).total_seconds()
                        except (TypeError, ValueError, OverflowError):
                            delay = 60
                    delay = max(60, delay)
                    print(
                        f"HTTP 429: límite de peticiones. Espera {delay:g} s antes "
                        "del siguiente intento.", file=sys.stderr, flush=True,
                    )
                    time.sleep(delay)
                    continue
                if exc.code in (401, 403):
                    raise RuntimeError(
                        f"Massive HTTP {exc.code}: comprueba MASSIVE_API_KEY y que tu "
                        "cuenta tenga habilitado Futures Basic. El acceso a acciones "
                        "no acredita acceso a Futures."
                    ) from None
                raise RuntimeError(f"Massive Futures devolvió HTTP {exc.code}.") from None
            except urllib.error.URLError as exc:
                raise ConnectionError(f"No se pudo conectar a Massive: {exc.reason}") from None
            if not isinstance(payload, dict) or payload.get("status") != "OK":
                raise RuntimeError("Massive Futures devolvió una respuesta no válida.")
            if not isinstance(payload.get("results"), list):
                raise RuntimeError("Massive Futures devolvió una respuesta sin results válidos.")
            print(
                f"Respuesta recibida: {len(payload['results'])} registros.",
                file=sys.stderr, flush=True,
            )
            return payload

    def _pages(self, url):
        seen = set()
        while url:
            if not isinstance(url, str) or url in seen:
                raise ValueError("Paginación de Massive repetida o no válida.")
            seen.add(url)
            print(f"Página {len(seen)} de la consulta.", file=sys.stderr, flush=True)
            payload = self._get_json(url)
            yield payload["results"]
            url = payload.get("next_url")

    def list_gold_contracts(self, start, end):
        """Une catálogos mensuales para recuperar también vencimientos ya terminados."""
        contracts = {}
        references = gold_reference_dates(start, end)
        for number, reference in enumerate(references, 1):
            print(
                f"Catálogo histórico GC [{number}/{len(references)}]: {reference}",
                file=sys.stderr, flush=True,
            )
            for item in self._gold_contracts_on(start, end, reference):
                contracts[item["ticker"]] = item
            print(
                f"Total de vencimientos GC encontrados: {len(contracts)}",
                file=sys.stderr, flush=True,
            )
        return sorted(contracts.values(), key=lambda item: (
            item.get("last_trade_date") or item.get("settlement_date") or "9999-12-31",
            item["ticker"],
        ))

    def _gold_contracts_on(self, start, end, reference):
        reference_date = reference.isoformat()
        params = {
            "product_code": "GC",
            "date": reference_date,
            "first_trade_date.lte": end.date().isoformat(),
            "last_trade_date.gte": start.date().isoformat(),
            "limit": 1000,
            "sort": "ticker.asc",
        }
        if reference >= date(2025, 3, 12):
            params["type"] = "single"
        query = urllib.parse.urlencode(params)
        contracts = {}
        print(
            f"Listado GC | fecha de referencia: {reference_date}",
            file=sys.stderr, flush=True,
        )
        for page in self._pages(f"{BASE_URL}/futures/v1/contracts?{query}"):
            for item in page:
                if item.get("product_code") != "GC":
                    raise RuntimeError(
                        "Massive devolvió un producto distinto de GC; se detiene "
                        "la consulta para no recorrer todo el mercado."
                    )
                if item.get("date", reference_date) != reference_date:
                    raise RuntimeError(
                        "Massive no respetó la fecha de referencia del listado; "
                        "se detiene la consulta para no recorrer fichas históricas."
                    )
                ticker = item.get("ticker", "")
                if (item.get("product_code") == "GC" and item.get("type") != "combo"
                        and GOLD_TICKER.fullmatch(ticker)):
                    if ticker in contracts:
                        raise RuntimeError(
                            f"Contrato {ticker} repetido en la fecha de referencia; "
                            "se detiene la paginación del listado."
                        )
                    contracts[ticker] = item
            print(
                f"Contratos GC únicos acumulados: {len(contracts)}",
                file=sys.stderr, flush=True,
            )
        return [contracts[ticker] for ticker in sorted(contracts)]

    def _download(self, ticker, start, end):
        if not GOLD_TICKER.fullmatch(ticker):
            raise ValueError("oro requiere un vencimiento simple de GC.")
        query = urllib.parse.urlencode({
            "resolution": "1min",
            "window_start.gte": timestamp_ns(start),
            "window_start.lt": timestamp_ns(end),
            "sort": "window_start.asc",
            "limit": 50000,
        })
        bars = []
        for page in self._pages(f"{BASE_URL}/futures/v1/aggs/{ticker}?{query}"):
            for item in page:
                seconds, nanos = divmod(item["window_start"], 1_000_000_000)
                moment = datetime.fromtimestamp(seconds, tz=timezone.utc)
                moment = moment.replace(microsecond=nanos // 1000)
                bars.append(MarketBar(
                    datetime=moment,
                    open=item["open"], high=item["high"], low=item["low"], close=item["close"],
                    volume=item["volume"], transactions=item.get("transactions"),
                ))
        return bars
