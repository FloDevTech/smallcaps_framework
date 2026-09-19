# Historial

Registro append-only de sesiones cerradas.

## 2026-09-19 — 1: unificar_reglas_sdd

- Aprobación: usuario respondió «si» a unificar las reglas y corregir contradicciones SDD, conservando archivos y sin implementar el framework.
- Alcance completado: reglas de colaboración y aprobación, flujo SDD proporcional, limpieza de arquitectura, comprobación de spec_ready y seguimiento.
- Documentación pequeña: propuesta aprobada en conversación como especificación; funciones nuevas: un archivo specs/<name>.md por defecto.
- Verificación: init.sh terminó con código 0; comprobación en memoria del validador: spec_ready aceptado, estado desconocido rechazado y dos tareas in_progress rechazadas. Revisión de coherencia entre documentos y estados.
- Se conservaron todos los archivos. No se modificó src/ ni se añadieron dependencias.
- Limitaciones: aún no hay tests del framework; init.sh selecciona Python del PATH y no garantiza usar venv/.

## 2026-09-19 — 2: validar_tickers

- Aprobado: CLI small_cli.py y JSON con TNMG/TRUG, fecha 18/09/2026 y 10 días.
- Implementado: lectura y validación, sin descarga ni dependencias nuevas; arquitectura y spec actualizadas.
- Verificación: 5 pruebas unittest pasan con Python de venv; ejecución manual correcta.
- Problema detectado: init.sh devuelve 0 pero omite tests por comandos find/grep de Windows. Se ejecutaron directamente; reparación del comprobador pendiente de autorización.

## 2026-09-19 — 3: corregir_deteccion_tests

- Aprobación: usuario respondió «si» a corregir únicamente la comprobación de pruebas en init.sh.
- Cambio: descubrimiento y ejecución mediante unittest de Python, sin find/grep ni dependencias adicionales.
- Verificación: init.sh ejecutó las cinco pruebas existentes correctamente. En copias temporales, una prueba fallida y un error de importación devolvieron código 1; sin directorio tests o con tests vacío se emitió aviso.
- Criterios cumplidos. No se modificaron CLI, JSON de datos ni selección del intérprete.
- Resuelto el problema de omisión de pruebas registrado en la tarea 2.

## 2026-09-19 — 4: configuracion_yaml

- Aprobado: PyYAML, migración del CLI y eliminación del JSON; ampliación a download con proveedor en config y comprobación de directorio.
- Se conservó E:\smallcaps_data; provider inicial schwab. Solo existe el comando download.
- Migración validada antes de retirar JSON; dependencia PyYAML 6.0.3 registrada.
- Verificación: 11 tests y comprobador correctos con venv en PATH. Comprobación real del destino correcta tras permiso adicional para E:.
- Interfaz común y módulos por proveedor documentados como siguiente etapa, aún sin implementar.
- Nota de entorno: bash del PATH resuelve WSL y la activación Git Bash carece de uname en este PATH; se verificó con Git Bash absoluto y venv/Scripts antepuesto temporalmente al PATH, sin modificar init.sh.

## 2026-09-19 — 5: identificadores_proveedores

- Petición explícita: cs = Charles Schwab, massive = Massive, ib = Interactive Brokers.
- Ajustados validador, valor actual de configuración, especificación y arquitectura. Ruta de datos conservada.
- Verificación: init.sh correcto con venv; 11 pruebas pasan, incluyendo aceptación de los tres códigos y rechazo del antiguo schwab y códigos desconocidos.
- Sin cambios en el comando único download ni implementación de conectores.

## 2026-09-19 — 6: contrato_descarga

- Aprobado: entidad e interfaz separadas de implementaciones; spread ask-bid opcional confirmado.
- Creados MarketBar y DataDownloader en src/download. Validación compartida de entrada/salida, sin conectores.
- Entidad con siete campos, validación OHLC y spread None cuando no existe dato. Intervalo interno [start, end) con zonas horarias.
- Arquitectura documenta la organización entidad/interfaz/implementaciones y el contrato.
- Verificación: 21 pruebas pasan con init.sh y venv; sin nuevas dependencias ni cambios al CLI.

## 2026-09-19 — 7: readme_base_massive

- Petición: README profesional, archivo de primera implementación Massive y opinión sobre almacenamiento.
- README ampliado: objetivo, avance, instalación, uso, esquema y roadmap; convertido de UTF-16 a UTF-8.
- massive.py creado con herencia del contrato y NotImplementedError explícito mientras falta la conexión.
- Parquet recomendado, decisión del usuario pendiente; no se implementó persistencia.
- Verificación: 23 pruebas pasan, enlaces locales comprobados y git diff --check correcto. No hubo commit ni push.

## 2026-09-19 — 8: migrar_flujo_sdd_openspec

- Aprobado: migrar del flujo SDD nativo al flujo openspec/ + Engram.
- Conservados: docs/architecture.md, docs/conventions.md, docs/verification.md, progress/history.md, specs/ (histórico), docs/CONTEXTO_PROYECTO.md y docs/contexto_recuperado/.
- Retirados: docs/specs.md, CHECKPOINTS.md, feature_list.json, progress/current.md, CODEX.md y .codex/agents/ (obsoletos). Sus reglas de colaboración se consolidaron en AGENTS.md.
- Actualizados: AGENTS.md, init.sh, README.md y docs/verification.md. Creados specs/README.md y openspec/changes/conectar-massive/proposal.md.
- Verificación: init.sh correcto (Entorno → Archivos base → Tests → Resumen); 23 pruebas unittest pasan con venv.
