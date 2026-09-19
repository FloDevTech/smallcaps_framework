# Presentación del proyecto y archivo inicial de Massive

## Alcance solicitado
El usuario pidió un README profesional para GitHub con objetivo y avance del framework, crear el archivo de la primera implementación (Massive) y comparar Parquet con DynamoDB.
Este paso prepara el archivo del proveedor; no desarrolla la conexión ni decide el almacenamiento por el usuario.

## Requisitos
- R1: README describe objetivo, estado real, instalación, configuración, uso, estructura, modelo y próximos pasos.
- R2: src/download/massive.py contiene MassiveDownloader derivado de DataDownloader, conservando la entidad y firma comunes.
- R3: Mientras no exista conexión, _download debe lanzar NotImplementedError explícito, sin devolver datos ficticios ni una lista vacía que simule éxito.
- R4: Documentar Massive como primer proveedor previsto; no cambiar el provider actual del usuario ni el comportamiento del CLI.
- R5: Comparar almacenamiento y dejar Parquet como recomendación pendiente de decisión; no instalar dependencias ni implementar persistencia.

## Diseño y pasos
- [x] Ampliar README.md existente (R1).
- [x] Crear massive.py con el punto de implementación explícito (R2–R3).
- [x] Verificar herencia, validación y error de funcionalidad pendiente; revisar documentación y regresiones (R1–R4).
- [x] Actualizar arquitectura y registrar la recomendación de almacenamiento sin darla por aprobada (R5).

No se realizan commits, push, peticiones a Massive ni escrituras en data_dir.

## Evidencia
- R1: README revisado contra estado y CLI; enlaces locales comprobados; UTF-8 y git diff --check correctos.
- R2–R3: tests/test_download_massive.py comprueba herencia, validación compartida y error explícito pendiente.
- R4: configuración y CLI sin cambios; pruebas de regresión pasan.
- R5: recomendación documentada como pendiente; sin implementación de almacenamiento ni nuevas dependencias.
- init.sh: 23 pruebas pasan. No se probó una descarga real ni se publicó en GitHub.
