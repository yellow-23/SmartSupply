# Caso de Estudio — SmartSupply Tesis

## Negocio de demostración

**Nombre:** Distribuidora El Ahorro (business_id = 18)
**Datos:** 9 familias de productos, ~168 días (nov 2025 – may 2026)
**Unidad:** pesos CLP (valores en el orden de 150k–600k por día)

## Cómo reproducir el caso (demo en vivo)

### 1. Registrarse y ver el onboarding

1. Ir a la URL del sistema
2. Registrar usuario: `demo@tesis.cl` / `demo1234`
3. El sistema crea automáticamente un negocio "Mi Distribuidora"
4. Dashboard muestra la pantalla de onboarding (aún sin datos)

### 2. Subir datos de ventas

1. Ir a **Ingesta**
2. Subir `ventas_distribuidor.xlsx` (o cualquier Excel con fechas, productos y ventas)
3. Stocky detecta las columnas automáticamente
4. Se muestra preview con calidad: rango de fechas, familias detectadas, advertencias
5. Confirmar carga → datos guardados en sales_history

### 3. Ver el Dashboard

- **SKUs en alerta**: N (todas las familias, porque stock inicial = 0)
- **Nivel de servicio**: 0% (sin stock configurado)
- **Gráfico de ventas**: últimos 28 días reales

### 4. Correr predicciones (AMS)

1. Ir a **Forecasting**
2. Seleccionar familia: BEBIDAS → horizonte 14 días → **Predecir**
3. El AMS evalúa ARIMA, Prophet, XGBoost, LSTM
4. Resultado: ganador con WAPE < 20% (validado en datos reales)
5. Repetir para ABARROTES, PANADERIA → modelos distintos ganan

**Resultado esperado del AMS (business 18):**
Ver `resultados_ams.txt` en esta carpeta (generado por `correr_ams.py`)

### 5. Ver Inventario

1. Ir a **Inventario**
2. Tabla muestra todas las familias como "Crítico" (stock=0 ≤ s calculado)
3. Hacer clic en BEBIDAS → ver EOQ, punto de reorden s, nivel S
4. Ver métricas: capital inmovilizado estimado, tasa de quiebre, nivel de servicio simulado

### 6. Generar Órdenes

1. Clic en **Generar órdenes automáticas**
2. Sistema crea N purchase_orders (una por familia crítica)
3. Ir a **Órdenes** → ver tabla con estado "Pendiente"
4. Confirmar una orden → estado pasa a "Confirmada"

### 7. Configurar parámetros con Stocky

1. Click en el botón naranja (Stocky) abajo a la derecha
2. Escribir: *"configura el stock actual de BEBIDAS en 500 unidades y el costo unitario en 950 pesos"*
3. Stocky actualiza la BD y confirma
4. Dashboard ahora muestra nivel_servicio > 0%

## Archivos de apoyo

| Archivo | Descripción |
|---------|-------------|
| `correr_ams.py` | Script que corre el AMS sobre el business y guarda resultados |
| `resultados_ams.txt` | Output del AMS: modelo ganador y WAPE por familia |
| `tabla_comparacion.py` | Genera la tabla AMS vs baseline para la tesis |

## Métricas para la tesis

La hipótesis se valida con esta tabla (ver `resultados_ams.txt`):

| Familia | Modelo AMS | WAPE AMS | WAPE ARIMA | Mejora |
|---------|-----------|----------|------------|--------|
| BEBIDAS | ? | ?% | ?% | ?pp |
| ABARROTES | ? | ?% | ?% | ?pp |
| ... | | | | |
| **Promedio** | AMS | **X%** | **Y%** | **Y-X pp** |

> La mejora en WAPE promedio valida que la selección automática por SKU
> supera al modelo único (ARIMA baseline).
