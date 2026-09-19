# Conectar Massive y decidir almacenamiento

## Why
Massive es el primer proveedor elegido; su archivo inicial (`src/download/massive.py`) está creado
pero la conexión lanza `NotImplementedError`. Faltan la descarga real y la decisión de
almacenamiento para avanzar con minería y backtesting.

## What Changes
1. Implementar el acceso real al proveedor Massive (autenticación, descarga y normalización)
   e integrarlo al comando `download` según `provider`.
2. Definir la conversión de `end_day`/`days` (días naturales vs sesiones) en el intervalo
   `[start, end)`.
3. Decidir el almacenamiento (recomendación: Parquet local + Polars; DynamoDB solo ante
   necesidad operativa) e implementar escritura incremental sin duplicados.

## Impact
- `src/download/massive.py` — implementación del conector.
- `src/small_cli.py` — integración con `download`.
- `docs/architecture.md` — decisiones de almacenamiento y calendario.
- `tests/` — pruebas del conector (sin conexión real) y de persistencia.
- `openspec/specs/` — delta specs de descarga y almacenamiento.

## Status
Proposal. Pendiente: specs → design → tasks → apply.
