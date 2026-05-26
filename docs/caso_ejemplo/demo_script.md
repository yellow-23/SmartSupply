# Script de Demo — Defensa de Tesis SmartSupply

## Contexto del caso

**Distribuidora El Ahorro**
- 9 familias de productos (ABARROTES, BEBIDAS, CARNES, CONGELADOS, FRUTAS, HIGIENE, LACTEOS, LIMPIEZA, PANADERIA)
- 168 días de datos reales (nov 2025 – may 2026)
- Usuario real ingestó datos desde Excel via el módulo de ingesta IA

---

## Flujo de demo (10 minutos)

### Parte 1 — Registro e ingesta (2 min)

1. Abrir la URL de producción
2. Registrar usuario `demo@tesis.cl` / `demo1234`
3. El sistema crea automáticamente el negocio y redirige al Dashboard
4. Pantalla de onboarding: "Sube tu primer archivo de ventas"
5. Ir a **Ingesta** → subir `ventas_distribuidor.xlsx`
6. Mostrar el preview: Stocky detectó 9 familias, rango de fechas, advertencias de calidad
7. Confirmar carga → 1395 registros cargados

**Punto clave para la tesis:** *"El sistema acepta cualquier Excel sin plantilla. Stocky interpreta las columnas automáticamente."*

---

### Parte 2 — Predicción AMS (4 min)

1. Ir a **Forecasting**
2. Seleccionar familia **BEBIDAS** → horizonte 14 días → Predecir
   - Mostrar gráfico: historial + predicción
   - Tarjeta del modelo ganador con WAPE%
3. Seleccionar familia **ABARROTES** → Predecir
   - Un modelo diferente puede ganar (o el mismo con WAPE distinto)
4. Seleccionar familia **PANADERIA Y PASTELERIA** → Predecir
   - Mostrar que Prophet detecta el cierre dominical

**Punto clave para la tesis:** *"El AMS selecciona automáticamente el mejor modelo por SKU. ARIMA puede ganar para series estables, Prophet para series con estacionalidad semanal clara. Eso reduce el MAPE global en X puntos porcentuales versus usar un solo modelo para todos los productos."*

> Mostrar tabla de comparación (de resultados_ams.txt):
> | Familia | Modelo AMS | WAPE AMS | WAPE ARIMA | Mejora |
> |---------|-----------|----------|------------|--------|
> | ...     | ...       | ...      | ...        | ...    |

---

### Parte 3 — Inventario y órdenes (3 min)

1. Ir a **Inventario**
2. Mostrar tabla: todas las familias en estado "Crítico" (stock inicial = 0)
3. Click en **BEBIDAS** → ver panel lateral:
   - EOQ calculado automáticamente
   - Punto de reorden s y nivel S
   - Capital inmovilizado estimado
4. Click en **Generar órdenes automáticas**
5. Ir a **Órdenes** → 9 órdenes pendientes creadas
6. Cambiar estado de una orden a "Confirmada"

**Punto clave para la tesis:** *"La política (s,S) se calibra automáticamente con los parámetros del producto. Sin SmartSupply, el jefe de bodega no sabe cuánto pedir. Con SmartSupply, recibe la cantidad óptima calculada por EOQ."*

---

### Parte 4 — Stocky (1 min)

1. Click en el botón naranja (Stocky) en cualquier página
2. Escribir: *"¿cuál es el estado del inventario de BEBIDAS?"*
3. Stocky consulta la BD y responde con stock, punto de reorden y EOQ
4. Escribir: *"actualiza el stock de BEBIDAS a 500 unidades"*
5. Stocky confirma y actualiza

**Punto clave para la tesis:** *"Stocky es el copiloto del jefe de bodega. Puede consultar y actualizar el inventario en lenguaje natural, sin navegar formularios."*

---

## Métricas clave para mostrar

| Métrica | Valor esperado | Fuente |
|---------|----------------|--------|
| WAPE promedio AMS | < WAPE ARIMA único | `resultados_ams.txt` |
| Familias con modelo distinto a ARIMA | ≥ 2 de 9 | `resultados_ams.txt` |
| Órdenes generadas automáticamente | 9 | Base de datos |
| Tiempo de ingesta (Excel → BD) | < 30 segundos | Demo en vivo |
| Tiempo de predicción por SKU | 30–90 segundos | Demo en vivo |

---

## Respuestas ante preguntas del jurado

**"¿Por qué no usan un solo modelo para todos los productos?"**
> "La hipótesis de la tesis dice que la heterogeneidad de patrones de demanda entre SKUs hace que un modelo único sea subóptimo. La tabla de resultados muestra que el modelo ganador varía por familia, y el WAPE promedio del AMS es X puntos menor al de ARIMA aplicado homogéneamente."

**"¿Cómo validan que el sistema funciona con datos chilenos reales?"**
> "El módulo de ingesta IA permite cargar datos de cualquier distribuidora chilena sin necesidad de ERP. Mostramos el caso de Distribuidora El Ahorro, cuyos datos reales pasaron por el pipeline completo: ingesta → forecasting → inventario → órdenes."

**"¿Qué pasa si la serie tiene menos de 30 días?"**
> "El sistema retorna un error informativo. Se requieren mínimo 30 días para el AMS. El validador de ingesta advierte al usuario si los datos son insuficientes."

**"¿Cómo se comparan los cuatro modelos?"**
> "ARIMA captura autocorrelación lineal. Prophet modela estacionalidades múltiples con feriados. XGBoost usa ingeniería de features (lags, promedios móviles, calendario). LSTM captura dependencias no lineales de largo plazo. El AMS evalúa los cuatro en validación walk-forward y elige el de menor WAPE."
