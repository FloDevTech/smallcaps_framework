# Evidencia de verificación — 19/10/2026

## Implementación

Comando `oro` añadido con aprobación del usuario. No se modificaron los YAML,
`src/download/massive.py`, el almacenamiento compartido ni las funciones de
`download`. Se añadieron dos módulos, pruebas y documentación; sin dependencias.

## Pruebas

- TDD: los dos archivos nuevos fallaron por módulos todavía inexistentes.
- Tras implementar: 19 pruebas nuevas pasan, sin usar API ni esperas reales.
- Comprueban discovery y paginación, vencidos y exclusión de combos,
  timestamps y límites, pausa en cada intento, 429 y agotamiento de reintentos,
  403 y falta de clave, respuestas inválidas, URL ajena y páginas repetidas,
  persistencia real Parquet, reanudación de vacíos y de fallos, ampliación de
  ventana, Parquet eliminado, fallo de escritura y separación del comando.
- Suite completa: 63 pruebas, 61 pasan; dos fallan al leer el YAML de acciones.
  En la comprobación inicial había un fallo porque esperaba TNMG/TRUG y el YAML
  contenía GCZ6/GCZ5. Durante la ejecución el YAML quedó con las solicitudes
  comentadas, por cambios externos a esta tarea. Se conserva tal cual.
- Se redirigió `tempfile.tempdir` solo en el proceso de pruebas a
  `C:\Users\FLODEV\AppData\Local\Temp`, porque el temporal predeterminado del
  sandbox producía errores de acceso. No se modificó el harness.
- `oro --help` devuelve 0; revisión del diff del CLI confirma una rama independiente.
- `git diff --check` sin errores; módulos y tests nuevos cumplen el límite de 100.

## Bloqueos y límites

- `init.sh`, ejecutado antes y después: Git Bash no arranca, error
  `NtCreateDirectoryObject / 0xC0000022` del entorno.
- Comprobación real de discovery con la clave de entorno: no pudo conectar,
  `getaddrinfo failed` (DNS). No se ha confirmado el acceso de la cuenta a Futures
  ni se ha realizado una descarga completa. No se expuso la clave.
- El comando está implementado y probado localmente; el change queda abierto,
  sin marcar cierre completo ni archivar mientras fallen comprobaciones.
- Un proceso por destino. La cuota no se coordina con otros procesos o aplicaciones.

## Repetir pruebas del alcance

## Seguimiento: consulta aparentemente bloqueada

El usuario compartió una salida que termina antes de `list_gold_contracts`,
después del aviso de pausa. Esa salida solo permite localizar la fase de consulta
de contratos; no distingue conexión, paginación o una espera por HTTP 429.

Se corrigió la falta de visibilidad dentro del proveedor de futuros: mensajes
inmediatos por stderr antes de cada pausa, al conectar, tras recibir resultados,
al paginar y antes de la espera adicional por 429. Se omiten clave y query/cursor.
No se modificaron peticiones, límites, reanudación ni el conector de acciones.

Prueba nueva ejecutada primero en rojo y después en verde: comprueba mensajes de
actividad, reintento y paginación sin revelar credenciales. Las 20 pruebas del
alcance pasan. `init.sh` continúa bloqueado por el mismo error de Git Bash.
No se afirma resuelto el bloqueo de red: es necesario repetir el comando desde
la terminal del usuario para identificar el punto concreto. No se inicia otra
descarga con la misma clave mientras pueda seguir activa la anterior.

### Comandos

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p test_massive_futures.py -v
.\venv\Scripts\python.exe -m unittest discover -s tests -p test_gold.py -v
```

## Seguimiento: página 174 en discovery

El usuario informa de 174 páginas. Revisado el código: la consulta no incluía
`type=single`, por lo que podía recibir combinaciones y descartarlas solo en
memoria. La documentación oficial confirma que omitir type incluye singles,
combos y valores vacíos. Se añade `type=single` al request de contratos y se
conserva la validación local, los filtros de fechas y la ausencia de active.

Regresión del filtro ejecutada primero en rojo, después en verde. Las 20 pruebas
del alcance pasan; no se lanzó otra consulta real con la clave del usuario.
La reducción efectiva de páginas y el resultado real siguen pendientes de
confirmación. El campo type no está disponible para consultas point-in-time
anteriores al 12/03/2025.

## Seguimiento: 120 páginas aun con type=single

El usuario aporta páginas 119/120 de contratos, con 1000 registros cada una. La
corrección anterior era insuficiente: se había omitido la fecha de referencia
del catálogo y solo se limitaban fechas de negociación. La API ofrece fichas
point-in-time; sin fijar `date` se podía recorrer su histórico y deduplicar al final.

Se añade `date` al día UTC del corte de datos y se conserva `type=single` sin
filtrar `active`. Se informa de contratos únicos por página. Se aborta si el
producto no es GC, la fecha recibida difiere de la solicitada o se repite un
vencimiento simple, en lugar de seguir haciendo peticiones.

Se consultaron las firmas del cliente oficial mediante Context7 y las fuentes:
- https://massive.com/docs/rest/futures/contracts
- https://massive.com/blog/futures-data-has-arrived
- https://massive.com/knowledge-base/article/how-do-i-get-intraday-bars-for-a-futures-contract
- https://massive.com/knowledge-base/article/does-massive-have-continuous-futures-contracts

Tres regresiones nuevas y el requisito de date fallaron antes del cambio.
Las 23 pruebas del alcance pasan después. Los casos incluyen vencidos,
rechazo temprano de versiones de otra fecha, contratos repetidos y otros productos.
No se modificaron small caps, sus YAML ni las pausas por petición. No se lanzó
otra descarga real: falta confirmar el resultado del endpoint con la cuenta del
usuario. No se marca el change como verificado por completo.

## Seguimiento: faltaban contratos ya vencidos en 2024

El usuario confirma que una consulta con date devuelve 34 contratos y descarga
barras de GCF7, pero señala que se están recorriendo vencimientos de 2028 sin
ver los terminados en 2024. Una sola foto actual del catálogo no garantiza incluir
vencimientos antiguos; la ausencia de active no es suficiente. La confirmación
anterior de que estaba avanzando no acreditaba cobertura de contratos vencidos.

Se sustituye la única foto por fotos mensuales de fecha explícita dentro de los
dos años, unidas por ticker. Se ordena por fecha de vencimiento ascendente para
descargar primero los antiguos. Los datos previos al comienzo del plan (hoy,
aproximadamente 19/10/2024) siguen fuera de cobertura. Se conserva reanudación y
todo lo descargado. Son aproximadamente 26 peticiones iniciales, cerca de seis
minutos con las pausas de 13 s, sin contar red o reintentos.

Antes de 12/03/2025 se omite type, pues Massive documenta que antes era null.
Las combinaciones se excluyen siempre por tipo cuando exista y por ticker simple.
Las fechas de referencia se desplazan fuera de fines de semana dentro del rango.
La granularidad mensual se apoya en el calendario de listado de GC por varios
meses; no se construyen tickers hipotéticos ni se descarga todo el historial de
versiones diarias del catálogo.

Fuente del calendario de listado GC:
https://www.cmegroup.com/market-regulation/files/gold-futures-and-options-fact-card.pdf

TDD: las pruebas fallaron antes de añadir la selección de fechas históricas.
Después pasan 25 pruebas del alcance, con un caso en el que GCZ4 solo figura en la
foto de 2024 y GCF7 sigue presente en 2026. Se prueba unión, deduplicación entre
fechas, orden por vencimiento y omisión de type en fechas antiguas. Falta verificar
la cobertura real de fotos históricas con la cuenta del usuario. Sin cambios a
small caps ni a la carpeta de datos existente.
