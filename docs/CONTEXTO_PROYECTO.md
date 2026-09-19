# Minado de datos SMALL CAPS — contexto recuperado

Recuperado el 19/09/2026 de las conversaciones accesibles. Raíz de trabajo: `D:\00_PROG\23_algo_trd\021_sm_framework`. Trabajar directamente aquí, sin trasladar el proyecto a un perfil de usuario.

## Fuentes y alcance de la recuperación

- `contexto_recuperado/definicion_original.md`: conversación «Proyecto de minado y ejecución», 7 turnos recuperados.
- `contexto_recuperado/integracion_maestra.md`: conversación «Integración Especificación Maestra», 6 turnos recuperados.
- `contexto_recuperado/abrir_proyecto.md`: conversación «Abrir proyecto cualquier lado», 4 turnos recuperados.
- `contexto_recuperado/arquitectura_sistema_cuantitativo.md`: copia del adjunto técnico original.

Las tres lecturas indicaron que no quedaban páginas adicionales. Se localizaron dos conversaciones asociadas al proyecto de ChatGPT y una conversación original externa vinculada por su contenido. Esto no acredita haber exportado todos los archivos o instrucciones internos del proyecto de ChatGPT. La imagen sobre la ubicación de Work no se ha incorporado. El documento editable/canvas mencionado por el asistente original no se expuso como adjunto: no se recuperó su texto literal.

## Objetivo y prioridades

Construir un framework Python/Polars para descubrir y validar patrones LONG de breakout en small caps, principalmente mediante acción del precio, volumen, VWAP, estructura y contexto fundamental. Priorizar calidad de señales. Primero minería dirigida de estructuras conocidas; después descubrimiento de patrones nuevos. ML inicial orientado a estimar probabilidad de alcanzar X R antes del stop. Deep Learning y ejecución automática en Charles Schwab quedan para fases posteriores.

MVP: Dataset → Setups → Outcomes → Validación → Alertas; el usuario opera manualmente.

## Decisiones recuperadas

- Universo: NASDAQ/NYSE, excluir acciones asiáticas, market cap <300 millones USD, precio ≤15 USD, float >1 millón.
- El usuario indicó float rotation >2. El asistente propuso conservarlo como variable/condición diaria en lugar de filtro del universo; no confundir esa propuesta con una confirmación explícita del umbral definitivo.
- Scanner aportado por el usuario: lista de acciones que habría operado y fecha target; cambio >10%, volumen >1,5×float, float y noticias True/False. Conservar también casos fallidos, sin seleccionar retrospectivamente solo ganadores.
- Unidad lógica: `(ticker, target_date)`. Apariciones en días consecutivos o tras días de inactividad son eventos distintos, aunque estadísticamente puedan estar relacionados.
- Contexto: diez días anteriores por evento. El asistente lo interpretó como diez sesiones; concretar calendario bursátil antes de implementar. Objetivo de histórico de hasta 150 días, sin asumir que Schwab entregue todo ese rango de una vez.
- OHLCV 1 minuto, inicialmente Schwab Price History; derivar contexto 5m y posiblemente diario. Disponibilidad efectiva, profundidad y cobertura horaria del proveedor pendientes de comprobar.
- Almacenamiento incremental con Parquet: separar `scanner_events` del histórico OHLCV por ticker; descargar intervalos faltantes sin duplicar barras cuando se solapen ventanas.
- Horario definitivo Nueva York/ET: 04:00–20:00. EARLY 04:00–08:29; PREMARKET 08:30–09:29; REGULAR 09:30–15:59; AFTERHOURS 16:00–20:00. Sustituye al horario anterior 08:30–20:00.
- Sesiones como contexto/variables, conservando continuidad: un patrón regular puede depender del premarket o early hours. Analizar diferencias de resultados por franja sin aislar su historia.
- Incluir contexto de D-1, D-2, etc. para investigar relaciones con patrones del día target; esas relaciones son hipótesis, no causalidad demostrada.
- Entrada inicial de referencia: cierre de la vela 1m que confirma el setup. Stop estructural dependiente del patrón, sin porcentaje universal.
- Éxito principal: cierre 1m en +3R o superior antes de alcanzar -1R; una mecha a 3R no basta. Para long, riesgo por acción = entrada − stop y nivel +3R = entrada + 3×riesgo.
- Guardar 1R, 1,5R, 2R, 3R, 4R, MFE, MAE, tiempos a objetivos, stop y confirmación de 3R por cierre. Separar detección del setup y evaluación posterior.
- Solo OHLCV histórico disponible; no existe bid/ask histórico confirmado. Comisión declarada: 0,01 USD «por transacción», con unidad aún sin aclarar.
- Validación temporal/walk-forward y fuera de muestra; evitar anticipación y división aleatoria que mezcle eventos muy relacionados. No fijar aún un porcentaje arbitrario de «alta probabilidad».

## Ideas propuestas para investigar, todavía no reglas cerradas

Familias: Holding VWAP, VWAP Reclaim, HOD Breakout, consolidación y ruptura, Red-to-Green. Features: niveles y volumen premarket/early, distancia a máximos previos, gap, volatilidad, volumen relativo, rotación del float, hora y día de semana. Ciclo del ticker: días desde apariciones previas, número de eventos recientes, máximos/volúmenes previos, resistencia del último impulso. Las definiciones exactas y su utilidad se validarán con datos.

## Jerarquía documental y estado real

El usuario pidió que `ESPECIFICACION_MAESTRA_V1.md` fuese la fuente principal de verdad. Las conversaciones posteriores aclaran que nunca se creó físicamente. Este archivo es una consolidación de contexto, no una copia literal de aquella especificación ni un cierre de decisiones pendientes.

El adjunto técnico queda como referencia secundaria. Su breakout de 60 velas, volumen ×4, precio sobre VWAP, riesgo máximo 1,5% y ejecución automática temprana no son requisitos definitivos. Su código es una plantilla antigua, no implementación validada.

La primera inspección no devolvió archivos. En la comprobación final aparecieron archivos de preparación del entorno (AGENTS.md, CODEX.md, CHECKPOINTS.md, init.sh, feature_list.json y .gitignore), que no fueron creados por esta recuperación. Ahora contiene también esta documentación y las fuentes recuperadas; en esta tarea no se ha implementado ni ejecutado el framework de trading.

El usuario había separado máquina de trabajo (conclusiones/diseño) y máquina de casa (cambios físicos). La ruta exigida es la raíz actual en D:, sin copias intermedias en C:.

## Pendientes para retomar

1. Redactar la especificación maestra física a partir de estas fuentes, señalando las decisiones abiertas.
2. Aclarar unidad de comisión, tratamiento definitivo de float rotation, criterio operativo de exclusión geográfica y selección de controles negativos fuera del scanner (no quedó definido un protocolo).
3. Precisar diez días naturales/sesiones, convención de timestamps y barra final, horizonte del outcome, casos sin objetivo/stop y ambigüedad intrabar con OHLCV.
4. Verificar acceso y cobertura Schwab, definir formato de entrada del scanner y política de datos faltantes.
5. Comenzar por scanner events + OHLCV + target_date + contexto, antes de ML avanzado o automatización.

Los puntos técnicos abiertos añadidos a esta lista son asuntos a resolver durante implementación; no se presentan como acuerdos previos del usuario.
