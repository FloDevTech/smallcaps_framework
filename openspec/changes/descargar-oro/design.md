# Diseño

`MassiveFuturesDownloader` hereda el contrato común `DataDownloader` y usa stdlib
HTTP, independiente de `MassiveDownloader`. La misma instancia regula discovery,
paginación y agregados. Una pausa antes de cada intento, incluido el primero,
evita ráfagas propias; otros procesos con la misma clave no están coordinados.

Discovery consulta fotos mensuales (`date` explícito) desde el inicio del intervalo
hasta su corte, incluyendo ambos extremos cuando hay día laborable disponible.
Se desplazan sábados y domingos para consultar un día de semana dentro del rango.
La unión por ticker recupera vencidos ausentes de la foto actual. Se conserva la
ficha más reciente encontrada y se ordena por last_trade_date/settlement_date.
Los GC tienen meses de cotización según su calendario de listado; las fotos
mensuales evitan descargar todas las versiones diarias de cada ficha.

Se fija `type=single` a partir del 12/03/2025; antes se omite porque type no existe.
La validación de ticker simple y exclusión de combos se mantiene en todos los casos.
No se filtra active. Se valida el producto, la fecha devuelta y la unicidad dentro
de cada foto; un ticker puede repetirse legítimamente en fotos de distintos meses.

`gold.py` reutiliza `ParquetStore` sin cambiarlo. Mantiene `_oro_progress.json`
con intervalos descargados por ticker. Solo confirma tras guardar todo el paquete.
Al reanudar resta intervalos cubiertos, conservando huecos y respuestas vacías.
Si un proceso cae entre Parquet y checkpoint se repite el paquete y se deduplica.
Los ficheros de datos y checkpoint deben conservarse juntos. Un único proceso oro
por destino; no se incorpora bloqueo ni ejecución concurrente.

La raíz explícita o configurada recibe la subcarpeta `oro`, con catálogo propio.
`provider`, `package_days`, `request_delay` y la lista de acciones no gobiernan oro.
Los valores de Basic son fijos, para no permitir superar el plan por configuración.

Fuentes oficiales consultadas el 19/10/2026:
- https://massive.com/futures
- https://massive.com/docs/rest/futures/contracts
- https://massive.com/docs/rest/futures/aggregates
