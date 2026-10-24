# Descargar oro con Massive Basic

## Propuesta y aprobación

Añadir `oro` a `src/small_cli.py`, con un proveedor de futuros independiente, sin
modificar el comportamiento de `download`, su conector ni los YAML de small caps.
El usuario aprobó este alcance el 19/10/2026: «si adelante».

Se descargarán todos los vencimientos GC con datos accesibles, barras 1m, dos años
de histórico y corte de ocho horas. Cada contrato tendrá su Parquet en una carpeta
separada. Se requiere paginación, reanudación y un mínimo de 13 segundos entre
peticiones, incluidos reintentos 429. Sin dependencias nuevas.

## Alcance de archivos

- `src/small_cli.py`: parser y rama de ejecución independientes para `oro`.
- `src/download/massive_futures.py`: acceso a futuros y límite de peticiones.
- `src/download/gold.py`: intervalos, persistencia y reanudación.
- Tests nuevos para ambos módulos y comando; documentación y evidencia del change.

## Estado inicial

44 pruebas existentes: 43 pasan; falla `test_default_from_another_directory` porque
espera TNMG/TRUG y el YAML del usuario contiene GCZ6/GCZ5. No se corregirá ese YAML.
`init.sh` no arranca: Git Bash devuelve NtCreateDirectoryObject / 0xC0000022.
Las pruebas usan temporalmente un directorio temporal permitido, sin editar el harness.

## Reversión

Retirar la rama `oro` y los módulos nuevos. Los datos de small caps no se modifican.
