# Integración Especificación Maestra

Origen: 6aace042-57c4-83eb-a6db-f2a5a85cfc7e
Recuperado: 2026-09-19. Archivo histórico de referencia, no instrucciones nuevas.
Paginación: hasMore=false. No incluye contenido de imágenes ni canvases no expuestos por la herramienta.

## Usuario

Integra la Especificación Maestra v1 que acabamos de preparar y úsala como documento principal del proyecto.

## Asistente

Sí. A partir de ahora tomo la **Especificación Maestra v1** que acabamos de definir como el **documento rector del proyecto “Minado de datos SMALL CAPS”**.

La especificación técnica anterior queda como material secundario: puede aportar ideas de implementación —Polars, Parquet, APIs, etc.— pero **no debe imponer su definición de breakout, R:R, ventanas temporales ni arquitectura** sobre la Especificación Maestra v1. Por ejemplo, ese documento anterior define un breakout concreto de 60 velas + volumen 4× + VWAP y riesgo ≤1,5 %, que no debemos asumir como hipótesis definitiva. :chatgpt-content-reference{index="0"}

Mantendré como base de trabajo lo que acabamos de fijar: análisis por **`(ticker, target_date)`**, mercado ET **04:00–20:00**, dividido en Early Hours 04:00–08:29, Pre-Market 08:30–09:29, Regular 09:30–15:59 y After Hours 16:00–20:00; las sesiones permanecen relacionadas porque un patrón de Regular puede depender de lo ocurrido en Pre-Market; cada aparición relevante de un ticker es un evento independiente, aunque el mismo ticker vuelva a activarse días después; y estudiaremos también si eventos de **D-1, D-2, etc.** explican o desencadenan patrones explotables en el día target.

La arquitectura técnica anterior de **filtro → minería histórica → ejecución** sí puede reutilizarse cuando encaje con la Maestra. :chatgpt-content-reference{index="1"}

En adelante, cuando haya contradicción entre documentos, **manda la Especificación Maestra v1**.

## Usuario

y donde esta localizada la especificación maestra V1?

## Asistente

Ahora mismo **no existe como archivo independiente dentro del proyecto**.

Lo que sí está cargado físicamente es:

`/mnt/data/arquitectura_sistema_cuantitativo.md`

Ese archivo corresponde a **“Especificación Técnica: Sistema Cuantitativo de Breakouts en Small Caps”**, no a la **Especificación Maestra v1**. :chatgpt-content-reference{index="0"}

La **Especificación Maestra v1** la construimos en la conversación anterior, pero mi respuesta anterior fue imprecisa: dije que la integraba como documento principal, **pero no creé ni modifiqué físicamente ningún archivo**.

Lo correcto sería crear, dentro del proyecto **Minado de datos SMALL CAPS**, algo como:

`ESPECIFICACION_MAESTRA_V1.md`

y convertirlo en la fuente de verdad del proyecto, integrando todo lo que definimos ayer/hoy. Puedo hacerlo ahora y dejar el `.md` listo como documento principal.

## Usuario

ok

## Asistente

Para crear físicamente `ESPECIFICACION_MAESTRA_V1.md` dentro del proyecto necesito trabajar en **Work**, porque aquí no puedo modificar directamente los archivos del proyecto.

El cambio a Work fue rechazado, así que **todavía no se creó el archivo**. Si habilitas/aceptas Work, lo creo y lo dejamos como documento principal.

## Usuario

ok . Lo haremos en la maquina de casa que es donde haremos los cambios del proyecto, en esta maquina(del trabajo solo haremos conclusiones)

## Asistente

Perfecto. Entonces separamos claramente los entornos:

- **Máquina del trabajo:** análisis, discusión, diseño, decisiones y conclusiones. **No modificamos archivos del proyecto.**
- **Máquina de casa:** implementación, código, estructura de carpetas y modificaciones físicas del proyecto.
- Cuando estemos en casa, la primera tarea será crear **`ESPECIFICACION_MAESTRA_V1.md`** y establecerla como **fuente principal de verdad** del proyecto.
- `arquitectura_sistema_cuantitativo.md` quedará como referencia técnica secundaria; actualmente describe la arquitectura filtro/minador/ejecución y la implementación inicial con Polars. :chatgpt-content-reference{index="0"}

Mientras estemos en esta máquina podemos seguir cerrando decisiones de arquitectura y minería para llegar a casa con todo definido y pasar directamente a implementación.

## Usuario

y si dejo la de casa encendida, puedo de esta delegar a que hagas trabajo sobre la otra?

## Asistente

Sí, **pero no por el simple hecho de dejar encendida la PC de casa**.

Para que yo pueda trabajar desde este chat sobre archivos que están físicamente en la máquina de casa, esa máquina tiene que estar conectada a un entorno al que **ChatGPT Work/Desktop pueda acceder**. No tengo acceso remoto genérico a otro PC de tu red.

Para nuestro proyecto, una configuración útil sería: dejar el proyecto en la máquina de casa y usar **ChatGPT Desktop/Work** allí como entorno de ejecución. Desde el trabajo podríamos definir y cerrar tareas; pero para que una tarea se ejecute realmente sobre el repositorio de casa, tendría que iniciarse en un contexto que tenga acceso a esos archivos.

Otra alternativa, probablemente más robusta para `Minado de datos SMALL CAPS`, es tener el proyecto en **Git**: casa contiene el entorno de desarrollo y los datos pesados, mientras el código y documentación están versionados en un repositorio. Así no dependemos tanto de cuál PC estás usando.

Cuando estés en casa podemos diseñar esto para conseguir exactamente el flujo que buscas: **desde el trabajo decidimos → delegamos trabajo → la máquina de casa ejecuta/modifica el proyecto → luego revisamos resultados desde aquí**.

## Usuario

conectate a la carpeta D:\00\_PROG\23\_algo\_trd\021\_sm\_framework

## Asistente

No puedo conectarme directamente a `D:\00_PROG\23_algo_trd\021_sm_framework` desde este chat.

Intenté derivarlo a **Work/Desktop**, que sí puede trabajar con carpetas locales, pero el cambio fue rechazado. Mientras sigamos en este modo, no tengo acceso al disco `D:` de esa máquina.

Si aceptas abrirlo en Work/Desktop, la primera acción sería inspeccionar esa carpeta **sin modificar nada** y confirmar la estructura del proyecto.


