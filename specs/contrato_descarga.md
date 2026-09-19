# Entidad e interfaz de descarga

## Alcance aprobado
El usuario pidió entidad, interfaz y posteriores implementaciones separadas por proveedor. Confirmó spread = ask − bid en unidades de precio, con None cuando no se facilite.
Este paso crea el núcleo común. No implementa proveedores, almacenamiento, credenciales ni conexiones desde el CLI.

## Requisitos
- R1: La entidad tiene exactamente datetime, open, high, low, close, volume y spread. Representa una barra de un minuto; spread es opcional y conserva cero como dato real.
- R2: Rechazar timestamps sin zona horaria, precios no positivos/no finitos, OHLC incoherente, volumen negativo/no entero y spread negativo/no finito.
- R3: Todos los proveedores derivan de DataDownloader y usan download(ticker, start, end), que devuelve list[MarketBar]. La interfaz no puede instanciarse sin implementar _download.
- R4: El núcleo común valida ticker no vacío, fechas con zona y start < end antes de llamar al proveedor. El intervalo interno es [start, end); datetime es el inicio de la barra.
- R5: Validar que el resultado sea una lista de MarketBar dentro del intervalo, ordenada ascendentemente y sin timestamps repetidos. Una lista vacía es válida si no hay barras; los errores del proveedor se propagan, no se convierten en lista vacía.
- R6: No añadir dependencias ni modificar el comportamiento del CLI.

## Diseño mínimo
- src/download/entity.py: dataclass inmutable MarketBar con validación de sus valores.
- src/download/interface.py: ABC DataDownloader; download contiene las comprobaciones comunes y _download es el punto abstracto que implementará cada proveedor.
- Los proveedores deben normalizar sus datos a esta entidad y contrato. No se rellenan barras ausentes ni se inventa spread.
- Se aceptan datetimes con zona sin imponer una conversión local silenciosa. La conversión de end_day/days al intervalo queda para la primera implementación.
- tests/test_download_entity.py y tests/test_download_interface.py: pruebas del contrato sin red ni archivos de datos.

## Pasos
- [x] Crear entidad y validar datos (R1–R2).
- [x] Crear interfaz y comprobaciones comunes (R3–R5).
- [x] Probar errores, rango, orden, spread y regresión del CLI (R1–R6).
- [x] Documentar arquitectura y registrar verificación.

## Evidencia
- R1–R2: tests/test_download_entity.py (campos, spread None/cero, OHLC, fecha, volumen e inmutabilidad).
- R3–R5: tests/test_download_interface.py (ABC, entradas, retorno, rango, orden, duplicados, zonas y propagación de errores).
- R6: las 11 pruebas existentes del CLI siguen pasando; no se cambiaron CLI ni dependencias.
- init.sh con venv: 21 pruebas correctas, código 0.
- Las clases de prueba no conectan a proveedores. No se ha verificado ninguna descarga real.
