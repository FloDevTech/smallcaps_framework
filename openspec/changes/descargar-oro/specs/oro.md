# Requisitos de oro

- El CLI MUST admitir `oro [--config RUTA] [--data-dir RUTA]` y conservar `download`.
- MUST usar MASSIVE_API_KEY y los endpoints `/futures/v1/contracts` y
  `/futures/v1/aggs/{ticker}`, sin añadir un SDK.
- MUST descubrir GC, sin restringir a contratos activos, filtrar por solapamiento
  de fechas y excluir combinaciones. MUST seguir toda la paginación.
- MUST solicitar `resolution=1min`, como máximo dos años naturales hacia atrás
  desde ahora y hasta ahora menos ocho horas, con límites UTC `[start, end)`.
- MUST dejar al menos 13 segundos entre intentos HTTP. Un 429 MUST esperar al
  menos 60 segundos (o Retry-After si es mayor) y reintentar hasta tres veces.
- MUST guardar cada vencimiento por separado, sin roll ni contrato continuo.
- MUST persistir paquetes completos de hasta 30 días y sus intervalos confirmados
  de forma atómica. Un intervalo vacío correcto MUST poder reanudarse sin repetirlo.
- Un fallo MUST devolver código distinto de cero; MUST NOT confirmarse el paquete
  fallido. Un 401/403 MUST explicar que se requiere acceso al producto Futures.
- El destino por defecto SHALL ser `data_dir/oro`; un destino explícito SHALL
  terminar también en una subcarpeta `oro` para aislar datos de acciones.

## Escenarios

Given contratos activos, vencidos y combinaciones, When se descubre GC, Then se
obtienen todos los vencimientos simples que solapan el histórico permitido.

Given varias páginas y un 429, When se descarga, Then todos los intentos respetan
la pausa, se siguen las páginas y se convierten nanosegundos a datetime UTC.

Given un paquete guardado y otro fallido, When se repite el comando, Then el
primero se omite y el segundo se repite sin duplicar las barras existentes.

Given un error de permisos de API, When se ejecuta oro, Then se informa el error
y no se anuncia descarga completa ni se altera el checkpoint del paquete fallido.
