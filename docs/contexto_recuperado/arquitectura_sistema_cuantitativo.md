# Especificación Técnica: Sistema Cuantitativo de Breakouts en Small Caps

Este documento define la arquitectura, el modelo matemático y la infraestructura de código necesaria para implementar un algoritmo de trading cuantitativo de momentum enfocado en **Breakouts de Alta Probabilidad y Alto Risk-Reward (R:R)** en acciones de baja capitalización (*Small Caps*), utilizando Python, Polars y el ecosistema API de Charles Schwab.

---

## 🏛️ 1. Arquitectura General del Sistema

Para garantizar el cumplimiento de los límites de tasa (*rate limits*) de las APIs y maximizar la velocidad de procesamiento, el sistema se estructura de forma desacoplada en tres módulos especializados:

1. **Módulo Filtro (El Embudo - Finviz/FMP):** Reduce diariamente el universo de más de 6,000 acciones de EE.UU. a una lista corta de entre 15 y 30 tickers con catalizadores inusuales de volatilidad y volumen durante el Pre-market.
2. **Módulo Minador (Investigación - Schwab Price History + Polars):** Descarga datos históricos intradía (barras de 1 minuto de los últimos 10 a 30 días) para analizar vectorialmente la ventaja estadística (*edge*) del patrón.
3. **Módulo Ejecución (Producción - Schwab Streamer WebSocket):** Se conecta al mercado en tiempo real, suscribe únicamente la lista corta de tickers filtrados, agrega los ticks en barras de 1 minuto en memoria y dispara órdenes automáticas.

---

## 🔬 2. Modelo Matemático del Breakout de Alta Probabilidad

El algoritmo valida una señal de compra exclusivamente si ocurre una confluencia de tres condiciones macro en la vela actual ($t$):

$$	ext{Breakout}_t = (Close_t > \max(High_{t-1 \dots t-60})) \ \land \ (Volume_t > 4 	imes \mu_{	ext{Volume}(20)}) \ \land \ (Close_t > VWAP_t)$$

### Gestión del Riesgo y Simetría R:R
Para asegurar que cada operación posea un perfil de **alto beneficio/riesgo**, el stop loss se define matemáticamente de forma restrictiva:
* **Precio de Entrada ($E$):** $Close_t$ al confirmarse la ruptura.
* **Stop Loss Técnico ($SL$):** $\min(Low_t, VWAP_t)$ o el mínimo del rango de consolidación inmediatamente anterior.
* **Filtro de Viabilidad:** Si la distancia porcentual del riesgo es superior al 1.5%, la operación se descarta automáticamente para evitar entrar en extensiones tardías y asegurar ratios de recompensa mínimos de 1:3 o 1:4.
$$	ext{Riesgo \%} = rac{E - SL}{E} \le 0.015$$

---

## 💻 3. Plantilla Base de Minería de Datos con Polars

A continuación se detalla la implementación optimizada utilizando las expresiones perezosas (*lazy*) de Polars para escanear el histórico intradía de Schwab de forma ultraveloz:

```python
import polars as pl

def minar_breakouts_high_prob(df_raw: pl.DataFrame) -> pl.DataFrame:
    """
    Procesa barras de 1 minuto históricas procedentes de Schwab para detectar setups.
    Columnas requeridas: ['ticker', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
    """
    # 1. Preparación del Pipeline de Ingeniería de Características (Lazy)
    df_features = df_raw.lazy().with_columns([
        # Máximo de la última hora (60 velas de 1 min) sin sesgo de futuro
        pl.col("high").rolling_max(window_size=60).shift(1).over("ticker").alias("max_60_min"),
        
        # Media móvil del volumen de las últimas 20 velas
        pl.col("volume").rolling_mean(window_size=20).over("ticker").alias("media_vol_20"),
        
        # Cálculo del VWAP acumulado intradía por sesión/ticker
        ((pl.col("volume") * pl.col("close")).cum_sum().over("ticker") / 
         pl.col("volume").cum_sum().over("ticker")).alias("vwap")
    ])
    
    # 2. Definición de filtros lógicos vectorizados
    condicion_precio = pl.col("close") > pl.col("max_60_min")
    condicion_volumen = pl.col("volume") > (pl.col("media_vol_20") * 4)
    condicion_institucional = pl.col("close") > pl.col("vwap")
    
    # 3. Filtrado y materialización en memoria
    breakouts = df_features.filter(
        condicion_precio & condicion_volumen & condicion_institucional
    ).collect()
    
    return breakouts
```

---

## 📅 4. Cronograma de Desarrollo Táctico

* [ ] **Fase 1: Conectividad y OAuth2:** Desarrollar el flujo de autenticación seguro de Schwab API, gestionando el intercambio del `auth_code` y la lógica de refresco automático del token de acceso (`access_token`).
* [ ] **Fase 2: Script de Extracción Histórica (EOD):** Crear un descargador robusto que consuma el endpoint `/marketdata/v1/pricehistory` usando parámetros Unix en milisegundos para capturar el histórico limpio en formato `.parquet`.
* [ ] **Fase 3: Optimización del Laboratorio:** Ejecutar el módulo de Polars sobre múltiples meses de datos acumulados para afinar el multiplicador de volumen óptimo y medir el factor de ganancia (*profit factor*).
* [ ] **Fase 4: Motor de Streaming en Vivo:** Implementar el cliente WebSocket para consumir el flujo de ticks en tiempo real, sincronizando un hilo estructurado de agregación temporal a barras exactas de 60 segundos.