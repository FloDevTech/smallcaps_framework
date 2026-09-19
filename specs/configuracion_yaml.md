# Configuración YAML y preparación de descarga

## Aprobación y alcance
El usuario aprobó PyYAML, la migración del CLI y retirar el JSON. Amplió el alcance para validar tickers y disponibilidad de data_dir con download, y después precisó: un único comando download, proveedor en configuración y futura interfaz común con un módulo derivado por proveedor.
Se conserva la ruta configurada por el usuario. No se implementan conexiones, autenticación ni descargas reales.

## Requisitos
- R1: config.yaml y tickers_download.yaml viven en src/config. Se conservan la ruta del usuario y los dos ejemplos.
- R2: La configuración exige data_dir (texto no vacío) y provider (cs, massive o ib). El valor actual es cs. Códigos actualizados por petición explícita del usuario: Charles Schwab, Massive e Interactive Brokers, respectivamente. Rutas relativas parten de la raíz del proyecto; rutas absolutas se respetan.
- R3: El único comando es download. Permite --config y --tickers para indicar otros YAML; sin comando muestra ayuda. No hay comandos download-cs ni download-massive.
- R4: Leer con safe_load y validar todas las solicitudes antes de comprobar el destino. Conservar las reglas de ticker, fecha DD/MM/AAAA y entero days > 0.
- R5: Comprobar que el destino existe, es directorio y permite crear, escribir y eliminar un archivo temporal. No crear el directorio ni alterar archivos existentes. Informar errores por stderr con código 1.
- R6: Si la preparación es correcta, mostrar proveedor, destino y solicitudes, con código 0 y aviso explícito de que no se han descargado datos. No comprobar credenciales ni conectividad.
- R7: Registrar PyYAML en requirements.txt, retirar JSON tras comprobar equivalencia y actualizar pruebas/documentación.

## Diseño
Funciones pequeñas en src/small_cli.py: lectura YAML, validación de solicitudes, carga de configuración, comprobación del destino y comando. PyYAML 6.0.3 instalado en venv con autorización.
La futura descarga tendrá una interfaz común y una implementación por proveedor; su contrato se definirá con la primera descarga. No añadir clases vacías ni módulos sin comportamiento ahora.
La sonda temporal sirve para comprobar escritura real, no solo permisos declarados. Se elimina al terminar.

## Pasos
- [x] Adaptar configuración y CLI. R1–R6.
- [x] Probar YAML, errores, rutas, directorio y comandos. R1–R6.
- [x] Retirar JSON, actualizar arquitectura y registrar verificación. R7.

## Verificación
- R1/R7: comparación JSON/YAML exacta antes de retirar el JSON; ruta E:\smallcaps_data conservada.
- R2: test_config_validation_and_relative_path.
- R3: test_only_download_command_and_help y test_default_from_another_directory.
- R4: test_example, test_invalid_requests, test_normalization_and_leap_day, test_file_errors_and_no_partial_success y test_invalid_tickers_stop_before_destination_probe.
- R5: test_destination_preserves_files_and_leaves_no_probe, test_destination_missing_file_and_write_denied y test_missing_destination_returns_error_without_success.
- R6: test_default_from_another_directory y ejecución real de download con destino E:\smallcaps_data (salida 0).
- Las 11 pruebas pasan; init.sh pasa con Python de venv en PATH.
- Comprobación del destino externo ejecutada con permiso adicional del entorno; sonda temporal eliminada. No se descargaron datos.
