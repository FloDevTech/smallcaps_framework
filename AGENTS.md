# Guía de trabajo — Small Caps

## Prioridad
Construir un framework simple, usable y verificable. Una tarea pequeña cada vez.
No añadir capas, herramientas, dependencias ni funcionalidades por si fueran necesarias en el futuro.

## Arranque
1. Lee docs/architecture.md, docs/conventions.md y openspec/config.yaml.
2. Revisa el change activo en openspec/changes/ (si lo hay) y progress/history.md.
3. Ejecuta bash ./init.sh. Si falla, informa; corrige solo dentro del alcance autorizado.
4. Trabaja únicamente en la tarea acordada con el usuario. No elijas otra automáticamente.

## Colaboración
- Antes de modificar, presentar el cambio concreto y pedir aprobación.
- La aprobación cubre los archivos y pasos del alcance acordado; no volver a pedirla para cada edición.
- Plantear una sola pregunta o decisión a la vez.
- Si el usuario o el agente propone ampliar el alcance, señalarlo y consultar antes de incorporarlo.
- Explicar resultado, comprobación y limitaciones con lenguaje claro.

## Fuentes
- openspec/config.yaml: flujo SDD, capacidades de testing y reglas de fase.
- docs/architecture.md: decisiones técnicas compartidas.
- docs/conventions.md: convenciones de código.
- docs/verification.md: comprobaciones (init.sh, unittest).
- progress/history.md: historial de cierres, sin borrar historia.
- specs/ y docs/CONTEXTO_PROYECTO.md: contexto histórico, no aprobación de cambios nuevos.

## Ejecución
El flujo SDD es proposal → specs → design → tasks → apply → archive (ver openspec/config.yaml).
Especificación aprobada → implementación acotada → verificación → cierre.
No marcar done con comprobaciones pendientes o fallidas.
Registrar aprobación y evidencia de verificación.
