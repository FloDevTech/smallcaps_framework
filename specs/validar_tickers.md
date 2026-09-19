# CLI de solicitudes de descarga

Especificación histórica: el formato JSON y la invocación inicial fueron sustituidos por YAML y el comando download en specs/configuracion_yaml.md.

## Aprobación y alcance
El 19/09/2026 el usuario aprobó recibir y validar tickers con fecha target, dejando la descarga para después, y pidió small_cli.py y tickers_download.json con TNMG y TRUG, end_day 18/09/2026 y days 10.
Esta especificación registra ese alcance aprobado. No incluye conexión al broker, descargas ni cálculo de intervalos bursátiles.

## Requisitos
- R1: El CLI DEBE leer por defecto tickers_download.json de la raíz del proyecto y permitir indicar otro archivo como argumento.
- R2: El archivo DEBE contener una lista no vacía de objetos con ticker (texto no vacío), end_day (fecha válida DD/MM/AAAA) y days (entero positivo, no booleano). Los campos desconocidos se rechazan para detectar errores de escritura.
- R3: Ante datos inválidos o archivo ilegible, el CLI DEBE informar por stderr y terminar con código 1 sin anunciar solicitudes válidas parciales.
- R4: Ante datos válidos, el CLI DEBE mostrar cada solicitud y terminar con código 0 sin descargar ni modificar datos.
- R5: El ejemplo DEBE incluir TNMG y TRUG con end_day 18/09/2026 y days 10.

## Diseño
src/small_cli.py usa solo la biblioteca estándar: argparse, json, datetime y pathlib. Funciones separadas para validar, cargar y ejecutar el CLI; sin nuevas capas.
tickers_download.json vive en la raíz. Se normaliza ticker quitando espacios exteriores y usando mayúsculas; no se comprueba su existencia en el mercado.
days se conserva como cantidad solicitada. Días naturales frente a sesiones, e inclusión de end_day, se decidirán al especificar la descarga.

## Pasos y verificación
- [x] Implementar lectura y validación (R1–R3).
- [x] Crear ejemplo y salida del CLI (R4–R5).
- [x] Probar ejemplo, errores de datos y archivos, y ejecución desde otra carpeta (R1–R5).
- [x] Ejecutar init.sh y registrar resultados.

## Resultado
Cinco pruebas pasan con venv/Scripts/python.exe -m unittest discover -s tests -v.
R1: test_default_from_another_directory y test_file_errors_and_no_partial_success.
R2: test_invalid_requests y test_normalization_and_leap_day.
R3: test_file_errors_and_no_partial_success.
R4: test_default_from_another_directory y ejecución manual del CLI.
R5: test_example.
init.sh termina con código 0, pero omite las pruebas por falta de grep y resolución incorrecta de find en este entorno. La ejecución directa de unittest es la evidencia de pruebas; reparar el comprobador queda pendiente fuera de este alcance.
