# Proyecto de minado y ejecución

Origen: 6aacd2c2-b280-83eb-8159-22b63ee2e9ce
Recuperado: 2026-09-19. Archivo histórico de referencia, no instrucciones nuevas.
Paginación: hasMore=false. No incluye contenido de imágenes ni canvases no expuestos por la herramienta.

## Usuario

Estoy armando un proyecto para minado de patrones en small caps y ejecución en un broker.
Las instrucciones del proyecto son las siguientes,
------------------------------
En este proyecto trataremos de hacer un framework:
     * Minar patrones dentro del mercado de las small caps, usando python, polars y librerias de Machine learning y deep learning, lo convierta en estrategias de compra y venta . 
     * Una vez encontradas las estrategias haremos la parte de  ejecución en charles schwab.
 
    * Lo que buscaremos en la estrategia son patrones de breakout de alta probabilidad y alto RR. Principalmente nos centraremos en la busqueda de acciones del precio. 

Trataremos de seguir la siguiente estrategia:
1) Busque de patrones que funcionen:
          * Buscaremos encontrar patrones en acciones que hayan funcionado en los ultimos días. Para este caso pasaremos acciones que hayan cumplido ciertos criterios fundamentales en los ultimos días y de ahí haremos el minado.
           * Luego del minado haremos backtesting, para ver la factibilidad
2) Hacer la parte de ejecucion
-----------------------
Ayudame a mejorar las instrucciones así el proyecto quede simple y factible. Preguntame lo que sea necesario para hacer el documento del proyecto, que sea la piedra angular de esto.

[User attached 1 file; file contents were not included]

## Asistente

Sí. Y antes de escribir el documento definitivo, cambiaría una cosa importante del planteamiento actual.

El documento adjunto ya propone una arquitectura **Filtro → Minador → Ejecución**, lo cual es una buena separación. :chatgpt-content-reference{index="0"} Pero en la parte de minería ya fija de antemano qué es un breakout: máximo de 60 velas + volumen ×4 + precio sobre VWAP. :chatgpt-content-reference{index="1"} Eso convierte el proyecto más en **optimización/backtest de una estrategia predefinida** que en **minería de patrones**.

Yo separaría claramente:

**datos → descubrimiento de patrones → validación → convertir patrón en estrategia → ejecución.**

Y dejaría ML/DL para después. Primero necesitamos demostrar que existe un edge explotable con métodos estadísticos y ML relativamente simple. Si eso funciona, tiene sentido probar redes neuronales.

Para hacer el documento que sirva realmente como piedra angular necesito cerrar estas decisiones. Respóndeme sin desarrollar demasiado; después yo estructuro todo.

1. **Universo inicial.** ¿Nos limitamos exclusivamente a small caps USA? ¿Qué rango aproximado de market cap quieres considerar?

2. **Selección diaria.** Dices que pasarás acciones que cumplieron determinados criterios fundamentales. ¿Qué información tendrás para cada ticker? Por ejemplo: gap %, volumen relativo, float, market cap, precio, news/catalyst, offering, dilution, short interest, etc. ¿O inicialmente quieres que el sistema reciba simplemente una lista de tickers seleccionada manualmente?

3. **Datos históricos.** ¿Qué fuente quieres utilizar para minería? El documento propone Schwab Price History y barras de 1 minuto de 10–30 días. :chatgpt-content-reference{index="2"} ¿Tenemos acceso confirmado a esos datos incluyendo **premarket + regular + after-hours**?

4. **Horizonte histórico.** Aquí haría un cambio importante: 10–30 días probablemente es demasiado poco para validar patrones. ¿Quieres comenzar almacenando datos desde ahora y trabajar inicialmente con, por ejemplo, 3–12 meses disponibles?

5. **Qué queremos descubrir.** Este punto es fundamental. ¿Quieres que el algoritmo descubra patrones que nosotros **no definimos previamente**, o quieres partir de estructuras conocidas —holding VWAP, VWAP reclaim, HOD breakout, consolidación, red-to-green, etc.— y buscar qué combinaciones producen mejores resultados? Mi propuesta sería hacer **ambas cosas**, pero empezar por la segunda porque es mucho más controlable.

6. **Variable objetivo.** Necesitamos definir matemáticamente qué significa que un patrón "funcionó". Por ejemplo: después de la señal, ¿alcanzó +2R antes de -1R?, ¿+3R antes de -1R?, ¿máximo favorable durante los próximos N minutos? Podríamos guardar varios outcomes y no decidir todavía uno único.

7. **Timeframe.** Entiendo que la ejecución principal será en **1 minuto**. ¿Quieres que el minado utilice también contexto de 5 min / diario, aunque la entrada se produzca en 1 min?

8. **Horario.** ¿Premarket + regular market, o sólo regular? Esto cambia mucho el comportamiento de small caps.

9. **Long/short.** Por lo que vienes trabajando, entiendo que la primera versión debería ser **solo long**. ¿Correcto?

10. **Risk/Reward.** El documento actual exige riesgo ≤1,5 % y busca 3R–4R. :chatgpt-content-reference{index="3"} Pero en tu trabajo manual reciente pasaste a **2R** porque 3R estaba descartando demasiados trades válidos. Para este proyecto preferiría **no fijar 2R, 3R o 4R de antemano**: que el dataset mida 1R, 1.5R, 2R, 3R, 4R y MFE/MAE. ¿Estás de acuerdo?

11. **Stop.** ¿Queremos que el SL sea siempre estructural —mínimo de consolidación, vela trigger, VWAP, nivel técnico— y que el algoritmo aprenda cuál funciona mejor? Evitaría un stop porcentual fijo como regla principal.

12. **Fundamentales/catalizadores.** ¿Quieres que formen parte del modelo de minería? Por ejemplo, descubrir que un determinado patrón funciona con float <10M + RVOL >5 + catalyst, pero no en el resto.

13. **Objetivo del ML.** Propongo que ML responda inicialmente una pregunta muy concreta: **dado el estado del mercado en este instante, ¿qué probabilidad tiene este setup de alcanzar X R antes del stop?** ¿Es lo que buscas?

14. **Ejecución.** Para la primera versión, ¿quieres que Schwab ejecute completamente automático o prefieres una fase intermedia de **alerta → paper trading → ejecución real**?

15. **Restricción principal.** ¿Qué priorizamos inicialmente: máxima precisión de señales aunque haya pocas operaciones, o encontrar más oportunidades aceptando menor precisión? Por lo que describes como "alta probabilidad y alto RR", interpreto **calidad antes que cantidad**.

### Arquitectura que propondría

Si confirmamos esas decisiones, simplificaría el proyecto a:

**FASE A — DATASET**  
Small caps seleccionadas → OHLCV 1m + contexto + fundamentales/catalizadores → Parquet.

**FASE B — PATTERN MINING**  
Cada instante se representa mediante features de **precio, volumen, VWAP, niveles, consolidación, volatilidad y contexto**. El sistema busca qué configuraciones preceden movimientos importantes.

**FASE C — OUTCOME ENGINE**  
Para cada posible señal calculamos qué ocurrió después:

`MFE | MAE | tiempo hasta 1R | 2R | 3R | stop primero | breakout failure`

Esta parte me parece especialmente importante porque nos permite cambiar después la definición de "buen trade" **sin volver a minar los datos**.

**FASE D — VALIDACIÓN**  
Train → validation → **walk-forward/out-of-sample**, respetando estrictamente el tiempo para evitar look-ahead/data leakage.

**FASE E — STRATEGY ENGINE**  
Patrón + contexto + probabilidad → entrada → SL estructural → target/gestión → position sizing.

**FASE F — EJECUCIÓN**  
Scanner → señal → Schwab streaming → orden → gestión → logging.

Y sólo cuando A–F funcionen:

**FASE G — ML avanzado / Deep Learning**

Esto evita empezar construyendo WebSockets, OAuth, redes neuronales y ejecución automática antes de saber siquiera si tenemos un patrón explotable.

Respóndeme **1–15**, aunque sea con frases cortas. Con eso preparo la **Especificación Maestra del Proyecto v1**, incluyendo objetivo, alcance/no-alcance, arquitectura, pipeline de datos, metodología de pattern mining, validación, backtesting, ejecución, estructura Python/Polars, fases y criterios objetivos para decidir cuándo podemos avanzar a la siguiente fase.

## Usuario

1. small caps que coticen en nasdaq y nyse y que no sean asiáticas por su alta dispersión. Market cap,<300M , precio <=15$, float >1M, float rotation >2
2. Los datos que cuento cada día para hacer el watchlist de operación son >10% cambio de precio +, volumen>1.5*float, float>1M,  si tiene o no noticias. 
3.  Schwab Price History y barras de 1 minuto de 10–30 días.
4. La idea son no mas de 150 días, por la cantidad de datos de minutos de cada acción.
5. ambas cosas, pero empezar por la segunda porque es mucho más controlable.
6. mínimo de 3R antes de 1R, el 3R debe ser con vela que cierre por encima del 3R y no un mechazo.
7. si
8. de 8:30 NY, hasta las 20 NY
9. nos centraremos en LONG (por ahora)
10. ok a que el dataset mida 1R, 1.5R, 2R, 3R, 4R y MFE/MAE. ¿Estás de acuerdo?
11. ok estructural
12. . OK
13. si
14. primera versión lo haremos con alertas y yo opero
15. Calidad

## Asistente

Perfecto. Con esto ya quedan definidos casi todos los límites importantes. Y haría dos ajustes conceptuales antes de congelar el documento maestro.

Primero, **float rotation >2 no lo pondría como filtro del universo**, sino como condición/evento diario. El universo puede ser `NASDAQ/NYSE + market cap < $300M + price ≤ $15 + float >1M + no asiáticas`; después, cada sesión seleccionamos cuáles tuvieron `price change >10%`, `volume >1.5×float`, noticias y otras variables. Así podremos descubrir posteriormente si float rotation 0.8, 1.5, 2, 4, etc. cambia radicalmente la probabilidad del patrón. Si filtramos previamente `>2`, perdemos esa información.

Segundo, separaría **la definición de éxito** de los outcomes almacenados. Tu criterio principal será:

**SUCCESS = alcanza 3R antes que -1R, y 3R se confirma mediante cierre de vela de 1 minuto ≥ 3R.**

Pero guardaremos 1R, 1.5R, 2R, 3R, 4R, MFE, MAE y tiempos. Esto nos permitirá descubrir, por ejemplo, que determinado patrón tiene 72% de alcanzar 2R pero sólo 38% de confirmar 3R, sin tener que recalcular todo el dataset.

### Esqueleto que ya podemos considerar definido

El objetivo del proyecto quedaría aproximadamente así:

> Construir un framework cuantitativo para descubrir, validar y posteriormente explotar patrones LONG de breakout en small caps de NASDAQ y NYSE, utilizando principalmente price action, volumen, VWAP, estructura de mercado y contexto fundamental/catalizadores.
>
> El sistema buscará patrones con alta probabilidad de producir movimientos de al menos 3R antes de alcanzar el stop estructural de -1R. Inicialmente el sistema generará alertas para ejecución manual. La automatización mediante Charles Schwab quedará para una fase posterior.

El universo base será:

`NASDAQ / NYSE → no asiáticas → Market Cap < $300M → Price ≤ $15 → Float > 1M`

Y cada **evento diario** tendrá variables como:

`Gap/change % | Volume | Float | Float Rotation | News YES/NO | Market Cap | Price`

Aquí hay una distinción muy importante: **no debemos guardar solamente los ganadores del día**. Necesitamos también ejemplos negativos. De lo contrario, el modelo aprendería sobre una muestra seleccionada únicamente porque ya sabemos que se movió.

El dataset intradía será de barras **1 minuto**, procedente inicialmente de Schwab Price History, hasta **150 días**, en horario **08:30–20:00 New York**. Además de 1m, construiremos features de contexto derivados de 5m y posiblemente diario; la entrada continuará siendo evaluada sobre 1m.

### Minería en dos etapas

**Etapa 1 — Pattern mining dirigido.** Empezamos por estructuras que conocemos: Holding VWAP, VWAP Reclaim, HOD Breakout, consolidación + breakout, Red-to-Green y otras que vayamos incorporando.

No vamos a decir simplemente *"VWAP reclaim funciona"*. Queremos descubrir algo del tipo:

> VWAP reclaim + consolidación determinada + RVOL elevado + float rotation X + distancia a HOD Y + volumen creciente + determinada hora del día → P(3R antes de -1R).

Eso ya es un problema de ML bastante concreto.

**Etapa 2 — Pattern discovery.** Una vez tengamos el dataset correctamente etiquetado, permitimos que algoritmos encuentren configuraciones que nosotros no hemos definido previamente.

Deep Learning queda fuera del MVP.

### La pieza crítica: Outcome Engine

Creo que esta debe convertirse en una de las partes centrales del framework.

Para **cada setup candidato**, guardamos algo parecido a:

`entry | structural_SL | R$ | hit_1R | hit_1.5R | hit_2R | hit_3R | close_confirm_3R | hit_4R | MFE_R | MAE_R | time_to_1R | time_to_2R | time_to_3R | stop_hit | outcome`

Esto desacopla completamente **detección** de **evaluación**.

Y además respeta tu condición especial: un wick que toque 3R **no cuenta como éxito de 3R**. Tiene que existir una vela de 1 minuto que cierre ≥3R antes de que se produzca el evento invalidante de -1R.

### Me faltan 6 decisiones

Estas sí conviene resolverlas antes de escribir la especificación maestra.

1. **Acciones negativas.** Si nuestra selección diaria exige `+10% y volumen >1.5×float`, ¿quieres guardar también acciones que cumplan el universo base pero **no** hayan explotado? Mi recomendación es **sí**, porque son esenciales como control.

2. **Noticias.** ¿Inicialmente basta `news = True/False`, o quieres guardar también tipo de catalyst: earnings, FDA, contract, offering, merger, etc.? Para MVP usaría `True/False` y posteriormente clasificación.

3. **Entrada.** Cuando detectamos un patrón histórico necesitamos determinar exactamente dónde habría entrado el algoritmo. Por ejemplo, cierre de la vela trigger. ¿Aceptamos inicialmente **entrada = close de la vela que confirma el setup**?

4. **Stop estructural.** Aquí tenemos varias posibilidades: low de trigger, low de consolidación, VWAP, último higher-low, etc. Mi propuesta es **no imponer uno universal**. Cada familia de patrón define sus candidatos de SL y el Outcome Engine compara resultados.

5. **Costes/slippage.** Para descubrir patrones podemos trabajar primero en precios puros, pero el backtest de estrategia debe incluir spread/slippage/comisiones. ¿Quieres que desde el principio almacenemos bid/ask si Schwab nos permite obtenerlo históricamente? Esto sería especialmente importante en small caps.

6. **Qué significa "alta probabilidad".** No hace falta decidirlo para minar, pero sí para convertir un patrón en estrategia. Por ejemplo, podríamos exigir un mínimo de muestras y posteriormente estudiar `P(3R antes de -1R)`. **No fijaría ahora un 60%, 70%, etc.** Dejaría que los datos nos muestren la distribución y después establecemos el umbral.

Con esas seis respuestas ya no seguiría agregando requisitos. Prepararía la **Especificación Maestra v1** y, muy importante, la mantendría deliberadamente simple: **Dataset → Setups → Outcomes → Validación → Alertas**. La ejecución automática en Schwab y Deep Learning quedarían explícitamente fuera del MVP. Esto además simplifica bastante el cronograma técnico que aparece actualmente en el documento, donde ya se plantea OAuth, extracción, optimización y WebSocket. :chatgpt-content-reference{index="0"}

## Usuario

1\) Si, para la parte de extraccion de datos pasare, listado de acciones que hubiera operado segun el scanner,  y el día target. bajaremos los 10 días anteriores para tener un contexto de cada acción. Pero puede darse que la acción aparezca 3 o 4 días seguidos en el scanner entonces tendremos un extracción de los ultimos 10 días. Confírmame si es optimo o lo hacemos de otra forma\_
2\) True/False
3\) Si.
4\) perfecto.
5\) solo tendremos los datos de OHLCV y la comisión que es 0.01 por transacción
6\) ok de acuerdo con esto que los datos hablen

## Asistente

Sí. Con esto ya podemos cerrar el diseño conceptual. Sobre el punto 1, haría una modificación porque te evitará duplicados y además nos dará un dataset bastante más limpio.

### Extracción: no descargaría 10 días cada vez

Tu idea es correcta conceptualmente: el **día target** es el día en que la acción apareció en el scanner, y necesitamos contexto anterior. Pero separaría **evento** de **datos de mercado**.

Ejemplo: imaginemos que `ABCD` aparece en el scanner:

```text
2026-09-01  ABCD
2026-09-02  ABCD
2026-09-03  ABCD
2026-09-08  ABCD
```

No descargaría cuatro bloques independientes de 10 días. Mantendría dos datasets.

**1. `scanner_events.parquet`**

```text
target_date | ticker | change_pct | volume | float | float_rotation | news
2026-09-01  | ABCD   | ...        | ...    | ...   | ...            | True
2026-09-02  | ABCD   | ...        | ...    | ...   | ...            | False
...
```

Cada fila representa **una aparición real en tu scanner**.

**2. Histórico OHLCV**

```text
data/ohlcv/
    ABCD.parquet
    XYZ.parquet
    ...
```

Para `ABCD`, calculamos el intervalo necesario una sola vez:

```text
primer target - 10 días  ──────────────────> último target
```

y descargamos únicamente lo que todavía no tenemos.

Así, si mañana vuelve a aparecer `ABCD`, **no descargamos nuevamente los últimos diez días**. Comprobamos hasta qué fecha tenemos OHLCV y agregamos solamente las barras nuevas.

Esto además encaja mejor con Polars/Parquet y nos prepara para aumentar posteriormente de 10 a 20, 50 o 150 días sin modificar la arquitectura.

### Los 10 días tienen otra función importante

Aquí haría una distinción:

**10 días de contexto ≠ 10 días de muestra.**

Si `ABCD` aparece el 18/09:

```text
08/09 ───────────────── 17/09 | 18/09
       CONTEXTO                 TARGET
```

Los diez días anteriores sirven para calcular cosas como estructura previa, highs/lows, volumen relativo, volatilidad, comportamiento respecto a VWAP, resistencia previa, etc.

Pero el **evento que estamos estudiando es el 18/09**.

Después tendremos miles de eventos:

```text
ABCD  18/09
XYZ   18/09
EFGH  19/09
ABCD  19/09
...
```

Esto evita cometer un error metodológico importante: tratar todas las velas de los diez días anteriores como si fueran señales equivalentes al día seleccionado por el scanner.

### Y mantendría las apariciones consecutivas

Si una acción aparece cuatro días seguidos:

```text
ABCD → lunes
ABCD → martes
ABCD → miércoles
ABCD → jueves
```

**son cuatro eventos distintos.**

No los eliminaría como duplicados.

De hecho, puede aparecer posteriormente una feature muy interesante:

```text
scanner_streak = 1
scanner_streak = 2
scanner_streak = 3
scanner_streak = 4
```

y también:

```text
days_since_first_scanner
```

Quizá descubramos que los breakouts del primer día tienen un comportamiento completamente diferente de los del tercer día. No debemos imponer una conclusión ahora; simplemente conservar la información.

---

## Entonces cierro las decisiones

El universo será **NASDAQ/NYSE, no asiáticas, Market Cap < $300M, precio ≤ $15 y float >1M**. El scanner aporta los eventos que realmente hubieras considerado operar: `change >10%`, `volume >1.5 × float`, float, float rotation y `news=True/False`.

Para cada evento descargamos OHLCV 1m con hasta **10 sesiones previas de contexto**, evitando descargas duplicadas mediante almacenamiento incremental en Parquet. Podemos conservar hasta 150 días cuando sea necesario.

El horario analizado será **08:30–20:00 NY** y empezamos exclusivamente **LONG**.

La entrada inicial será:

```text
Entry = Close de la vela 1m que confirma el setup
```

El stop será **estructural y dependiente del patrón**, no un porcentaje fijo.

El Outcome Engine calculará:

```text
1R
1.5R
2R
3R
4R
MFE
MAE
time_to_XR
stop_hit
```

Y nuestro outcome principal será:

```text
SUCCESS =
    cierre de vela 1m >= 3R
    ANTES de alcanzar -1R
```

Un wick a 3R **no cuenta como éxito**.

Tendremos solamente OHLCV para reconstruir el mercado. Por tanto, no intentaremos simular bid/ask histórico que no tenemos.

Sobre la comisión necesito únicamente precisar una cosa en el documento: cuando dices **$0.01 por transacción**, necesito saber si significa **$0.01 por acción negociada**, que es como veníamos trabajando en tu plan manual, o literalmente **$0.01 por orden/trade independientemente del número de acciones**. Son modelos de coste completamente distintos. 

Y no fijaremos arbitrariamente qué significa "alta probabilidad". Primero obtenemos la distribución real de `P(3R antes de -1R)`, número de muestras, estabilidad temporal, etc., y después establecemos los criterios para aceptar una estrategia.

Con la aclaración de esos **$0.01**, ya tenemos suficiente. El siguiente paso sería redactar la **Especificación Maestra v1**; no añadiría más requisitos por ahora.

## Usuario

cambiaremos lo siguiente empezaremos de 4:00 am a 8:00 pm, y haremos la distinción entre early hour, de 4 a 8:29, pre market de 8:30 a 9:29, de 9:30 a 15:59 horario regular y de 16:00 hasta las 20 after hour

## Asistente

Sí. Lo incorporaría como una **clasificación temporal explícita** del dataset, no solo como horario de descarga.

Queda así, siempre en **hora de Nueva York (ET)**:

| Sesión | Horario ET |
|---|---|
| **Early Hours** | 04:00 – 08:29 |
| **Pre-Market** | 08:30 – 09:29 |
| **Regular Market** | 09:30 – 15:59 |
| **After Hours** | 16:00 – 20:00 |

Cada barra de 1 minuto tendrá una variable categórica:

```text
session =
    EARLY
    PREMARKET
    REGULAR
    AFTERHOURS
```

Esto será importante para el minado. **No mezclaría inicialmente las estadísticas de las cuatro sesiones**, porque un mismo patrón puede tener comportamientos muy diferentes a las 6:30, 9:15, 9:35 o 17:00.

Además guardaría features temporales simples:

```text
session
minutes_from_0400
minutes_from_regular_open
minutes_to_regular_open
minutes_from_regular_close
day_of_week
```

Así podremos descubrir relaciones como:

> Un determinado HOD breakout tiene una probabilidad de 3R diferente en Early Hours, Pre-Market o durante los primeros minutos de Regular Market.

Y mantendremos **1 minuto como timeframe base**, construyendo posteriormente 5m y otros contextos desde esas barras.

Por tanto, reemplazamos en la especificación anterior **08:30–20:00** por **04:00–20:00 ET con cuatro regímenes temporales explícitos**.

Solo sigue pendiente confirmar el coste: entiendo que los **$0.01 son por acción negociada**, no $0.01 por orden. Si es así, con eso cerramos requisitos y podemos pasar a la **Especificación Maestra v1**.

## Usuario

1\) ten en cuenta que ciertos patrones en horarios regulares se dan por comportamientos en premarket.
2\) el día target puede ser muy diferente en cada acción, esto diferencial en small caps, hay acciones que hacen su desarrollo un día y mueren. y otras que explotan hoy y luego por 10 días no pasa nada y vuelven a explotar luego a los 12 dias. por ejemplo

## Asistente

Correcto. Esos dos puntos cambian cómo debemos pensar el dataset. **La unidad de análisis no debe ser ni la sesión aislada ni simplemente el ticker: debe ser el evento `ticker + target_date`, acompañado de su historia previa.**

### 1. Las sesiones no son independientes

La clasificación `EARLY / PREMARKET / REGULAR / AFTERHOURS` sirve como **feature**, pero no debemos fragmentar el análisis.

Por ejemplo, un breakout a las 10:05 puede depender de algo ocurrido a las 07:20:

```text
04:00                08:30    09:30                    16:00
│ EARLY                │ PRE │ REGULAR                   │
│                      │     │                           │
│     ┌── spike ──┐    │     │                           │
│     │           │____│_____| consolidación → BREAKOUT │
│                      │     │                           │
└─────────────────────────────────────────────────────────→

        CONTEXTO ───────────────────────► SEÑAL
```

Por tanto, para una señal de Regular Market podremos tener features como:

```text
premarket_high
premarket_low
premarket_volume
premarket_range
premarket_change_pct

early_high
early_low
early_volume

distance_to_premarket_high
distance_to_premarket_low

broke_premarket_high
held_premarket_high
premarket_high_tests

gap_at_0930
volume_before_0930
```

Y lo mismo con estructuras más complejas.

Por ejemplo:

**Premarket spike → pullback → hold VWAP → apertura → reclaim PM high → breakout**

debería poder aparecer como **un patrón completo**, aunque atraviese varias de nuestras categorías temporales.

Por eso las sesiones son **regímenes/contexto**, no datasets independientes.

---

### 2. `target_date` pasa a ser fundamental

Coincido con tu segundo punto. En small caps no podemos pensar:

> "ABCD es una acción que tiene este comportamiento."

Tenemos que pensar:

> "¿Qué estaba ocurriendo con ABCD alrededor del evento del 18/09?"

La misma acción puede producir:

```text
Ticker ABCD

Día 1   ██████████████   explosión
Día 2   ███████
Día 3   ██
Día 4   ▏
...
Día 10  ▏
Día 11  ██
Día 12  ███████████████  nueva explosión
```

Por eso dos apariciones separadas:

```text
ABCD | 2026-09-01
ABCD | 2026-09-12
```

son **dos eventos target diferentes**, aunque pertenezcan al mismo ticker.

Y cada uno tiene su propio contexto.

### Entonces modificaría también mi propuesta de los 10 días

Mantengo el almacenamiento OHLCV incremental por ticker para no descargar datos duplicados.

Pero **lógicamente**, para minería construiremos una ventana alrededor de cada `target_date`.

Por ejemplo:

```text
                  TARGET
                    ↓
D-10 ... D-3 D-2 D-1 | D0
─────────────────────┼────────────────
      CONTEXTO       │ DÍA ESTUDIADO
```

Si vuelve a aparecer doce días después:

```text
                              TARGET 2
                                  ↓
         D-10 ............... D-1 | D0
──────────────────────────────────┼────
              CONTEXTO            │
```

Los datos OHLCV físicos pueden solaparse. **Los eventos estadísticos no.**

Esto nos permite posteriormente crear algo que creo que será extremadamente relevante para small caps: el **lifecycle del ticker**.

Por ejemplo:

```text
days_since_last_scanner_event
days_since_first_scanner_event

scanner_events_last_3d
scanner_events_last_5d
scanner_events_last_10d

max_change_last_10d
max_volume_last_10d

previous_run_high
distance_previous_run_high

previous_day_runner = True/False
multi_day_runner = True/False
```

Pero no definiría todavía qué es un *multi-day runner*. **Lo medimos primero y dejamos que los datos indiquen qué importa.**

### Hay además una consecuencia importante para ML

Tenemos que impedir que el modelo considere dos eventos muy próximos del mismo ticker como observaciones completamente independientes.

Por ejemplo:

```text
ABCD  Sept 10
ABCD  Sept 11
ABCD  Sept 12
ABCD  Sept 13
```

comparten muchísimo contexto.

Esto será relevante cuando hagamos `train / validation / test`: **no podremos hacer un random split convencional de filas**, porque tendríamos leakage entre eventos relacionados.

La validación tendrá que ser **temporal / walk-forward**, manteniendo la cronología.

---

Por tanto, incorporaría dos principios explícitos a la Especificación Maestra:

> **Principio de continuidad intradía:** Early Hours, Pre-Market, Regular Market y After Hours son regímenes temporales utilizados como features. No son mercados independientes. Un patrón puede comenzar en una sesión y resolverse en otra.

> **Principio de evento:** la unidad fundamental del dataset será `(ticker, target_date)`. Cada target representa una aparición independiente del scanner y será analizada utilizando su contexto histórico previo, aunque existan otros targets anteriores o posteriores para el mismo ticker.

Esto deja la arquitectura mucho mejor adaptada a cómo se comportan realmente las small caps y evita que el framework termine siendo simplemente un detector de velas.

## Usuario

perfecto, aparte es posible que se pueda encontrar que eventos que ocurren un día desencadenan al otro día un patrón explotable.
ok, armame el documento para pasarle al proyecto y poder comenzar mañana a trabajar desde casa

## Asistente

He creado un espacio de trabajo separado para preparar la **Especificación Maestra v1** como documento editable.

He incluido también el punto que acabas de añadir: **un evento ocurrido en D-1, D-2, etc. puede formar parte causal/contextual de un patrón explotable en el día target**, por lo que el minado no quedará limitado a patrones puramente intradía.

La especificación queda orientada a que mañana puedas empezar directamente por **Día 1**, sin entrar todavía en Deep Learning ni ejecución automática: primero construir correctamente `scanner events + OHLCV + target_date + contexto`.

## Usuario

me lo puede fusionar con el proyecto denominado "minado de datos SMALL CAPS"?

## Asistente

Sí, pero no puedo fusionar directamente dos chats/proyectos desde esta conversación.

Si **“minado de datos SMALL CAPS”** es un proyecto de ChatGPT, lo correcto es mover/continuar allí el trabajo y usar la **Especificación Maestra v1** que acabamos de definir como documento central del proyecto. Así mantenemos en un único sitio arquitectura, decisiones, código y evolución.

Si quieres, abre **“minado de datos SMALL CAPS”** y dime allí simplemente:

> “Integra la Especificación Maestra v1 que acabamos de preparar y úsala como documento principal del proyecto.”

Y continuamos desde ahí con el **Día 1 de implementación**.


