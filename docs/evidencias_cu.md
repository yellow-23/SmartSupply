# Evidencias de ejecucion CU-16 a CU-43

App: https://smartsupply-frontend.pages.dev (negocio con datos cargados, ej. Santa elene)
API (Swagger): https://smartsupply-e6g8.onrender.com/docs

Mismo estilo que CU-01..15: ventana completa del navegador con la URL visible.
Nombre de archivo: `CU-XX.png` (si hay dos, `CU-XX-a.png`, `CU-XX-b.png`).

## Token para Swagger (CU-21, 22, 23)

Esos endpoints no tienen pantalla propia en la app; la evidencia es la respuesta en Swagger.
1. Con sesion iniciada en la app: DevTools > Application > Local Storage > `sb-xqiehkshtedrodhtdkzv-auth-token` > copiar `access_token`.
2. En /docs: boton "Authorize", pegar el token (sin "Bearer").
3. Abrir el endpoint, "Try it out", llenar parametros, "Execute". Capturar parametros + respuesta 200.

## Lista

| CU | Donde | Que hacer | Que debe verse |
|----|-------|-----------|----------------|
| 16 | /ingest | Subir un Excel de catalogo/lista de precios (con costo, lead time) | Preview clasificado como catalogo con los campos detectados y el boton Confirmar; segunda captura con el mensaje de productos actualizados |
| 17 | /ingest | Con un preview activo, preguntar a Stocky "esta bien para cargar?" | Panel de quality issues + respuesta de Stocky mencionando cargas previas/solape |
| 18 | /datos | Negocio > ubicacion > tabla de cargas; Revertir una carga | a) dialogo de confirmacion, b) carga con estado "reverted" |
| 19 | /datos | Expandir una carga, editar la venta de una fila inline | Fila en modo edicion y luego con el valor nuevo |
| 20 | /datos | Expandir una carga, borrar una fila | Confirmacion de borrado o la tabla sin la fila |
| 21 | Swagger | GET /api/sales/date-range con business_id | JSON con fecha minima y maxima |
| 22 | Swagger (o /forecasting) | GET /api/sales/history con business_id, family, store_nbr | JSON con la serie; alternativa: grafico historico en Forecast |
| 23 | Swagger | GET /api/sales/summary con business_id | JSON con familias ordenadas por total |
| 24 | /forecasting | Elegir SKU + tienda, Generar | Grafico historico + prediccion y tarjeta del modelo ganador con WAPE |
| 25 | /forecasting | Cambiar horizonte a 30 dias | Selector en 30 y grafico con 30 dias proyectados |
| 26 | /forecasting | Boton Exportar | PDF abierto (resumen + tabla) |
| 27 | /forecasting | Selector "Datos: Dataset de referencia" | Prediccion sobre Favorita con modelo ganador |
| 28 | /inventory | Boton Generar ordenes | Mensaje de ordenes creadas; luego /orders con las nuevas en "pending" |
| 29 | /orders | Cambiar estado de una orden (pending -> confirmed) | Selector de estado y la orden con el estado nuevo |
| 30 | /orders | Aplicar filtro por estado | Tabla filtrada + contador por estado |
| 31 | /orders | Boton Exportar Excel | Excel abierto con las ordenes |
| 32 | /inventory | Boton Exportar Excel | Excel abierto con las alertas |
| 33 | /products | Crear o editar un producto | Formulario con costo/lead time y la tabla actualizada |
| 34 | Stocky flotante | "que productos estan en riesgo?" | Respuesta con datos reales del negocio |
| 35 | Stocky flotante | "el costo unitario de BEBIDAS es 1200 y el lead time 5 dias" | Confirmacion de Stocky; opcional /products con el valor cambiado |
| 36 | Stocky flotante | "tengo 80 unidades de LACTEOS en bodega" | Confirmacion; opcional /inventory con el stock nuevo |
| 37 | Stocky flotante | "que productos les falta configurar?" | Lista de productos con campos vacios |
| 38 | /dashboard | Abrir | Fila de KPIs (alertas, ordenes pendientes, MAPE, nivel de servicio) |
| 39 | /dashboard | Correr antes un forecast en /forecasting | Grafico con ventas reales + serie de prediccion |
| 40 | /dashboard | Abrir | Panel de alertas criticas |
| 41 | /forgot-password | Ingresar correo, enviar; abrir el correo; /reset-password | a) mensaje de envio, b) correo recibido, c) formulario de nueva clave |
| 42 | /admin (cuenta platform_admin) | Tabla de usuarios; cambiar rol o desactivar uno de prueba | Tabla de usuarios y el cambio aplicado |
| 43 | /admin | Eliminar un negocio de prueba | Dialogo de confirmacion irreversible y la lista sin el negocio |

Para 42 y 43 usar un usuario/negocio de prueba creado para esto, no uno real.
