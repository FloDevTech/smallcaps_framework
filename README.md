# Small Caps Framework

Framework en Python para construir datasets históricos, investigar patrones LONG en small caps y validar estrategias antes de generar alertas para ejecución manual.

**Estado: infraestructura de datos en desarrollo.** Ya existen el CLI de preparación, la configuración YAML, la entidad de barra y el contrato común de descarga. Massive será el primer proveedor: su archivo inicial está creado, pero la conexión todavía no está implementada.

## Objetivo

Investigar qué combinaciones de acción del precio, volumen, niveles y contexto preceden movimientos favorables en small caps de NASDAQ y NYSE. La unidad de análisis será **`(ticker, target_date)`**, conservando la historia previa y las relaciones entre sesiones y días.

```text
Selección de tickers → Datos históricos → Setups → Outcomes → Validación → Alertas
```

La prioridad es un sistema simple, reproducible y usable. Primero se construirán los datos y la evaluación de patrones. La ejecución automática y el Deep Learning quedan para fases posteriores.

## Alcance de investigación previsto

- Barras de **1 minuto** y contexto histórico por evento.
- Horario **04:00–20:00, Nueva York**, con cuatro franjas: Early, Pre-Market, Regular y After Hours.
- Continuidad entre sesiones: un patrón regular puede depender del premarket o de días anteriores.
- Entrada de referencia al cierre de la vela de confirmación y stop estructural según el patrón.
- Criterio principal: cierre en **+3R antes del stop de −1R**; una mecha a 3R no basta.
- Medición adicional de 1R, 1,5R, 2R, 4R, MFE, MAE y tiempos hasta objetivos.
- Validación temporal fuera de muestra antes de convertir patrones en estrategias.

Estos son objetivos del proyecto, no capacidades ya implementadas ni resultados de rentabilidad.

## Avance

| Componente | Estado |
| --- | --- |
| Configuración y solicitudes YAML | Implementado |
| Comando download: validación de solicitudes y destino | Implementado |
| Entidad MarketBar y validación OHLCV/spread | Implementado |
| Interfaz común DataDownloader | Implementado |
| Archivo del proveedor Massive | Implementado (REST 1m) |
| Descarga incremental y almacenamiento Parquet | Implementado (solo massive) |
| Catálogo de datos por ticker y período | Implementado |
| Logging persistente con rotación | Implementado |
| Minería, outcomes, backtesting y alertas | Pendiente |

## Inicio rápido — Windows / PowerShell

Desde la raíz del repositorio, con Python instalado:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Si ya existe `venv`, basta con instalar los requisitos. El código utiliza Python 3.9+; el entorno de desarrollo se ha verificado con Python 3.14. Dependencias: PyYAML, Polars y tzdata.

### Configuración

Edita `src/config/config.yaml` con una carpeta existente y accesible:

```yaml
data_dir: data
dir_log: data  # directorio para archivos de log
provider: massive  # cs: Charles Schwab; massive: Massive; ib: Interactive Brokers
package_days: 10   # descarga en paquetes de N días
```

Las rutas relativas parten de la raíz del proyecto. También se admiten rutas absolutas. Para usar el ejemplo local, crea la carpeta una sola vez:

```powershell
New-Item -ItemType Directory -Force data
```

La configuración del repositorio puede contener una ruta propia del equipo: ajústala antes de ejecutar. Los códigos de proveedor se validan; solo `massive` activa una conexión real. Para descargar, define la variable de entorno `MASSIVE_API_KEY` con tu clave de Massive.

### Solicitudes

Edita `src/config/tickers_download.yaml`:

```yaml
- ticker: TNMG
  end_day: "18/09/2026"
  days: 10

- ticker: TRUG
  end_day: "18/09/2026"
  days: 10
```

`end_day` requiere una fecha válida `DD/MM/AAAA` y `days` un entero positivo. El intervalo de descarga es `[end_day - days, end_day)` en días naturales UTC; la interpretación de sesiones bursátiles queda pendiente.

### Ejecutar

```powershell
.\venv\Scripts\python.exe src\small_cli.py download
```

Con `provider: massive`, el comando descarga las barras 1m de cada ticker en `data_dir/{TICKER}.parquet`, dividiendo el rango en paquetes de `package_days` días y de forma incremental: conserva lo ya descargado y agrega solo las barras faltantes. Requiere la variable `MASSIVE_API_KEY`. Con otro proveedor, valida la configuración e indica que la descarga aún no está implementada.

Para consultar qué datos están disponibles:

```powershell
.\venv\Scripts\python.exe src\small_cli.py catalog
```

Muestra el catálogo con cada descarga registrada: ticker, período descargado (start/end), cantidad de barras y timestamp. El mismo ticker puede aparecer en múltiples filas si se descargó en períodos no contiguos.

Para indicar otros archivos:

```powershell
.\venv\Scripts\python.exe src\small_cli.py download --config ruta\config.yaml --tickers ruta\tickers.yaml
```

Sin comando muestra ayuda. Los errores de validación terminan con código distinto de cero.

## Estructura

```text
src/
├── small_cli.py
├── logger.py            # Configuración de logging persistente
├── config/
│   ├── config.yaml
│   └── tickers_download.yaml
├── download/
│   ├── entity.py        # Entidad MarketBar
│   ├── interface.py     # Contrato y validación común
│   └── massive.py       # Proveedor Massive (REST)
└── storage/
    ├── parquet_store.py # Almacenamiento Parquet por ticker
    └── catalog.py       # Catálogo de datos descargados
tests/                 # Pruebas sin conexión a proveedores
openspec/              # Flujo SDD: config, specs y changes
specs/                 # Especificaciones históricas (funciones cerradas)
docs/                  # Arquitectura, convenciones y contexto
progress/              # Historial de trabajo
requirements.txt       # Dependencias
```

Cada módulo separa **entidad, interfaz e implementaciones**. Se añaden componentes cuando existe una necesidad concreta y aprobada.

## Contrato de datos

| Campo | Significado |
| --- | --- |
| datetime | Inicio de la barra con zona horaria (UTC) |
| open, high, low, close | Precios OHLC |
| volume | Volumen entero no negativo |
| spread | ask − bid en unidades de precio; None si no está disponible |
| transactions | Número de transacciones de la barra; None si no está disponible |

Los proveedores heredan `DataDownloader` e implementan `_download(ticker, start, end)`. El método público `download` valida entradas y resultados: devuelve una lista de `MarketBar`, ordenada, sin duplicados y dentro del intervalo **`[start, end)`**.

El spread ausente no se sustituye por cero ni se deduce de OHLC. `transactions` es opcional: se llena cuando el proveedor lo entrega (Massive lo entrega). Un error del proveedor tampoco se convierte en una lista vacía.

## Almacenamiento

Las barras se guardan en **Parquet local con Polars**, un archivo por ticker en `data_dir/{TICKER}.parquet`. La escritura es incremental: se conservan las barras existentes (deduplicación por `datetime`) y se agregan solo las faltantes, con escritura atómica. DynamoDB se evaluaría si apareciera una necesidad concreta de consultas operativas compartidas en AWS.

Referencias: [Apache Parquet](https://parquet.apache.org/docs/overview/), [lectura Parquet en Polars](https://docs.pola.rs/api/python/stable/reference/api/polars.scan_parquet.html) y [consultas y escaneos en DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html).

## Catálogo de datos

El catálogo (`data_dir/_catalog.parquet`) registra cada descarga como una fila independiente: ticker, período descargado (start/end), cantidad de barras y timestamp de la descarga. Si un mismo ticker se descarga en períodos no contiguos, aparecen múltiples filas, permitiendo ver gaps reales en los datos.

El campo `bars` refleja las barras efectivamente agregadas al parquet (después de deduplicar), no el total recibido del proveedor.

Ejemplo de catálogo con descargas no contiguas:

```
TRUG | 2026-05-28 10:00 → 2026-06-06 16:00 | 2800 bars
TRUG | 2026-09-09 09:30 → 2026-09-18 16:00 | 3500 bars
TNMG | 2026-09-09 09:30 → 2026-09-18 16:00 | 2500 bars
```

El comando `catalog` muestra este DataFrame completo para inspección.

## Logging

El framework registra todas las operaciones en archivos de log con rotación automática. El archivo activo es `dir_log/last.log`. Cuando supera 50 líneas, se renombra a `dir_log/YYYYMMDDHHmm.log` (con sufijo `_N` si ya existe uno con ese timestamp) y se crea un nuevo `last.log`.

Formato de cada línea:

```
2026-09-19 14:30:00 | INFO | smallcaps | Descarga completada.
```

Los logs también se imprimen en consola con formato corto (`INFO: mensaje`).

## Verificación

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

El comprobador `init.sh` revisa la estructura, los estados y las pruebas. Requiere Git Bash y el Python de `venv` disponible en el PATH. Las instrucciones están en [docs/verification.md](docs/verification.md).

Las pruebas actuales verifican contratos y preparación local; no acreditan acceso a APIs ni cobertura histórica de ningún plan de datos.

## Próximos pasos

1. Especificar y desarrollar la conexión con Massive, incluyendo autenticación y normalización.
2. Acordar calendario, intervalo y cobertura del histórico solicitado.
3. Elegir el almacenamiento e implementar escritura incremental sin duplicados.
4. Construir el dataset de eventos, setups y outcomes.
5. Validar patrones y generar alertas para ejecución manual.

## Forma de trabajo

Seguimos **SDD** con el flujo `openspec/` + Engram (proposal → specs → design → tasks → apply → archive), una tarea acotada cada vez. Las decisiones técnicas se mantienen en [docs/architecture.md](docs/architecture.md), las convenciones en [docs/conventions.md](docs/conventions.md) y la verificación en [docs/verification.md](docs/verification.md). El contexto histórico está en [docs/CONTEXTO_PROYECTO.md](docs/CONTEXTO_PROYECTO.md).
