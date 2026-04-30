# Convenciones de Ramas y Commits — SmartSupply

## Ramas

| Prefijo | Uso | Ejemplo |
|---------|-----|---------|
| `main` | Rama principal. Siempre debe compilar y correr. | `main` |
| `feat/` | Nueva funcionalidad | `feat/ams-selector` |
| `fix/` | Corrección de bug | `fix/mape-division-by-zero` |
| `docs/` | Solo cambios de documentación | `docs/marco-teorico-v2` |
| `exp/` | Experimentos, notebooks, análisis exploratorio | `exp/lstm-hyperparams` |
| `refactor/` | Refactoring sin cambios de funcionalidad | `refactor/etl-clean` |

### Reglas de ramas

- **Nunca commitear directamente a `main`** salvo el setup inicial.
- Crear PR (Pull Request) para mergear a `main`. Al menos 1 integrante debe revisar.
- Borrar la rama después del merge.
- Las ramas de experimentos (`exp/`) pueden mergearse sin PR si son solo notebooks.

---

## Commits

Seguimos el estándar **Conventional Commits**:

```
<tipo>(<módulo>): <descripción corta en español>
```

### Tipos permitidos

| Tipo | Cuándo usarlo |
|------|---------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `test` | Agregar o modificar tests |
| `refactor` | Refactoring sin cambios de comportamiento |
| `chore` | Tareas de mantenimiento (deps, config) |
| `exp` | Experimentos / notebooks exploratorios |

### Módulos

| Módulo | Descripción |
|--------|-------------|
| `forecasting` | Módulo de predicción de demanda |
| `inventory` | Módulo de gestión de inventario |
| `backend` | API REST FastAPI |
| `etl` | Pipeline de datos |
| `frontend` | Dashboard React |
| `docs` | Documentos de tesis |

### Ejemplos de buenos commits

```
feat(forecasting): implementar modelo ARIMA con auto_arima por SKU
feat(inventory): agregar cálculo de punto de reorden política (s,S)
feat(backend): agregar endpoint GET /api/forecast/{sku_id}
feat(etl): script de limpieza y normalización del dataset Kaggle
fix(forecasting): manejar MAPE indefinido cuando demanda es cero
docs(docs): agregar marco teórico forecasting versión final
exp(forecasting): notebook EDA exploratorio dataset Store Sales
chore(backend): actualizar requirements.txt con versiones fijas
```

### Ejemplos de commits a evitar

```
fix: arregle cosas          ← demasiado vago
update                      ← no dice nada
feat: agregué todo          ← demasiado amplio
WIP                         ← nunca commitear WIP a main
```

---

## Flujo de trabajo sugerido

```bash
# 1. Partir desde main actualizado
git checkout main
git pull origin main

# 2. Crear rama para la tarea
git checkout -b feat/forecasting-prophet-model

# 3. Trabajar, commitear frecuente con mensajes descriptivos
git add forecasting/src/prophet_model.py
git commit -m "feat(forecasting): implementar ProphetModel con soporte de feriados chilenos"

# 4. Subir la rama
git push origin feat/forecasting-prophet-model

# 5. Crear Pull Request en GitHub → pedir review
# 6. Merge a main → borrar rama
```

---

## .gitignore — Archivos que NO se suben al repo

```
forecasting/data/           # CSV del dataset (muy pesado, va en .gitignore)
forecasting/models/         # Modelos entrenados (.pkl, .pt)
**/__pycache__/
**/*.pyc
**/.env
**/venv/
**/node_modules/
*.zip                       # Excepto en datasets/ donde ya está el .zip original
```

---

*Convenciones acordadas por el equipo — Mayo 2025*
