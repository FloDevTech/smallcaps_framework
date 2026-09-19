# Arquitectura del framework Small Caps

Este archivo recoge decisiones técnicas compartidas y aprobadas.
Los requisitos de cada función viven en su especificación; el contexto histórico no sustituye su aprobación.

## Principios
- Añadir módulos conforme los necesitemos, con responsabilidades claras.
- Preferir funciones simples y comprobables; evitar capas y abstracciones anticipadas.
- Mantener dependencias mínimas. Proponer y justificar cualquier incorporación antes de usarla.
- Separar cálculo y acceso a datos cuando facilite probarlos, sin imponer capas adicionales.
- Comunicar errores explícitamente; no ocultar fallos como resultados vacíos o exitosos.
- En una interfaz de comandos, informar errores por stderr y devolver un código distinto de cero.
- Evitar lecturas y escrituras repetidas innecesarias; definir la estrategia según el volumen real.
- No añadir un sistema de configuración hasta que exista una necesidad aprobada.

## Estado
El comando download prepara la descarga: valida configuración, solicitudes y destino.
Todavía no conecta con proveedores ni descarga datos.

## Entrada de solicitudes
- `src/config/tickers_download.yaml`: lista de objetos con ticker, end_day (DD/MM/AAAA) y days (entero positivo). Sustituye al JSON original.
- `src/config/config.yaml`: data_dir y provider. Se respeta la ruta configurada por el usuario; las rutas relativas parten de la raíz del proyecto.
- `provider`: cs (Charles Schwab), massive (Massive) o ib (Interactive Brokers); selección actual cs. Identifica el futuro proveedor, no certifica que esté conectado.
- `src/small_cli.py`: lee YAML con PyYAML safe_load, valida toda la lista y comprueba que el destino existe y permite escribir mediante un archivo temporal que se elimina.
- Ejecución desde la raíz: `venv/Scripts/python.exe src/small_cli.py download`.
- Opciones de download: `--config ruta.yaml` y `--tickers ruta.yaml`. Las rutas por defecto se resuelven respecto al proyecto. Sin comando muestra ayuda.
- PyYAML 6.0.3 es la única dependencia externa actual; instalación en venv desde requirements.txt.
- Las funciones de carga y validación están separadas de la salida del CLI; no hay capas adicionales.
- Semántica de días naturales/sesiones y límites del intervalo pendiente de la especificación de descarga.
- Requisitos iniciales: `specs/validar_tickers.md`; migración y comportamiento vigente: `specs/configuracion_yaml.md`.

## Organización de módulos
Por petición del usuario, cada módulo se organiza con entidad, interfaz e implementaciones en archivos separados. Añadir las implementaciones cuando se desarrolle su comportamiento.

## Núcleo de descarga
- `src/download/entity.py`: MarketBar, entidad inmutable con datetime, open, high, low, close, volume y spread.
- datetime identifica el inicio de la barra 1m y requiere zona horaria. Precios y spread se expresan en unidades de precio; volume es un entero no negativo.
- spread = ask − bid; None significa dato no disponible, cero es un valor real. No se calcula a partir de OHLC ni se rellena artificialmente.
- `src/download/interface.py`: DataDownloader es la clase abstracta común. download(ticker, start, end) valida y llama a _download, implementado por cada proveedor.
- Intervalo interno [start, end), inicio incluido y fin excluido, con zona horaria. Retorno: list[MarketBar] ordenada y sin timestamps duplicados ni fuera de rango.
- Una lista vacía significa ausencia de barras, nunca un error de red ocultado. Se propagan errores del proveedor.
- Las implementaciones deben heredar y conservar download; @final expresa esta restricción para herramientas de tipado, pero Python no impide sobrescribirlo en ejecución. Las implementaciones futuras deberán verificar el contrato con pruebas.
- Contrato y evidencia: `specs/contrato_descarga.md`. Sin dependencias nuevas.

## Siguiente etapa
Massive será la primera implementación. Su archivo src/download/massive.py contiene MassiveDownloader, derivado de DataDownloader; la conexión aún lanza NotImplementedError explícito. No está conectado al CLI.
Desarrollar el acceso real al proveedor y conectarlo al único comando download según provider. La conversión de end_day/days en inicio y fin sigue pendiente.

## Almacenamiento propuesto — pendiente de decisión
Recomendación: Parquet local para las barras históricas y Polars para análisis. El formato columnar y la lectura selectiva encajan con minería y backtesting por lotes. DynamoDB se consideraría ante una necesidad de consultas operativas en AWS; no se incorpora en esta fase.
La partición de archivos y la persistencia se especificarán al aprobar el almacenamiento. No mezclar distintos proveedores sin conservar su procedencia.
Referencias: https://parquet.apache.org/docs/overview/ y https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html.
