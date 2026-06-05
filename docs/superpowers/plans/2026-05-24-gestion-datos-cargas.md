# Gestion de datos y cargas (ingest_log) - Plan de Implementacion

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hacer auditable y flexible la data ingestada: cada fila sabe de que carga vino y quien la subio; el usuario administra varios negocios con varias ubicaciones y gestiona sus cargas (ver / editar / revertir) desde una pagina nueva, con asistencia de Stocky.

**Architecture:** Se agrega `ingest_log` (una fila por carga) y `sales_history.ingest_id`. El confirm deja de hacer UPSERT: cada carga inserta filas propias. El solape entre cargas se resuelve al consultar (ultima gana + solo activas) via una vista SQL. El front gana una pagina "Datos" con drill-down Negocio -> Ubicacion -> Cargas y un selector de destino en el flujo de ingesta.

**Tech Stack:** FastAPI 0.111, SQLAlchemy 2.0, Pydantic v2, PostgreSQL (Supabase), React + Vite + TanStack Query + Zustand, anthropic SDK (Stocky).

**Nota sobre testing:** El proyecto no tiene pytest. La verificacion de cada tarea de backend se hace arrancando `uvicorn app.main:app --reload` y probando el endpoint en `http://localhost:8000/docs` o con `curl`. La verificacion de frontend se hace en `npm run dev` (http://localhost:5173). Cada tarea de backend incluye el comando `curl` exacto con la respuesta esperada.

**Como correr (referencia):**
```bash
# Backend
source venv/bin/activate && cd backend && uvicorn app.main:app --reload
# Frontend
cd frontend && npm run dev
# Token para curl (reemplazar credenciales):
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"cristobal@distribuidora.cl","password":"demo1234"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
```

---

## FASE 1 - Base de datos y modelos

### Task 1: Migracion SQL del esquema

**Files:**
- Create: `backend/scripts/migrate_s3_ingest_log.sql`

- [ ] **Step 1: Escribir el script de migracion**

```sql
-- backend/scripts/migrate_s3_ingest_log.sql
-- Sprint 3: gestion de datos y cargas (ingest_log)
-- Aplicar en Supabase SQL editor o via psql.

-- 1) Owner de negocio: un negocio pertenece a un usuario
ALTER TABLE businesses
  ADD COLUMN IF NOT EXISTS owner_user_id INTEGER REFERENCES users(id);

-- 2) Tabla de cargas
CREATE TABLE IF NOT EXISTS ingest_log (
  id               SERIAL PRIMARY KEY,
  business_id      INTEGER NOT NULL REFERENCES businesses(id),
  store_nbr        INTEGER NOT NULL,
  user_id          INTEGER NOT NULL REFERENCES users(id),
  filename         VARCHAR NOT NULL,
  file_type        VARCHAR NOT NULL,
  records_loaded   INTEGER NOT NULL DEFAULT 0,
  sales_unit       VARCHAR(10) NOT NULL DEFAULT 'units',
  date_range_start DATE,
  date_range_end   DATE,
  families         JSONB,
  status           VARCHAR(10) NOT NULL DEFAULT 'active',
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ingest_log_business ON ingest_log(business_id, store_nbr);

-- 3) Cada fila de ventas sabe de que carga vino
ALTER TABLE sales_history
  ADD COLUMN IF NOT EXISTS ingest_id INTEGER REFERENCES ingest_log(id);
CREATE INDEX IF NOT EXISTS ix_sales_history_ingest ON sales_history(ingest_id);

-- 4) Cambiar la unicidad para permitir cargas separadas por el mismo dia+familia
ALTER TABLE sales_history DROP CONSTRAINT IF EXISTS sales_history_business_id_date_family_store_nbr_key;
ALTER TABLE sales_history
  ADD CONSTRAINT uq_sales_history_load
  UNIQUE (business_id, store_nbr, date, family, ingest_id);
```

- [ ] **Step 2: Aplicar la migracion en Supabase**

Aplicar el contenido del archivo via el SQL editor de Supabase (proyecto `xqiehkshtedrodhtdkzv`) o via MCP `apply_migration`. Si la DB esta pausada, restaurarla primero desde el dashboard.

Nota: el nombre real de la constraint vieja puede diferir. Verificar con:
```sql
SELECT conname FROM pg_constraint WHERE conrelid = 'sales_history'::regclass AND contype = 'u';
```
y ajustar el `DROP CONSTRAINT` con el nombre que devuelva.

- [ ] **Step 3: Verificar el esquema**

```sql
\d ingest_log
\d sales_history
```
Esperado: `ingest_log` existe; `sales_history` tiene columna `ingest_id` y constraint `uq_sales_history_load`.

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/migrate_s3_ingest_log.sql
git commit -m "feat(s3): migracion SQL ingest_log + ingest_id en sales_history"
```

---

### Task 2: Modelos ORM

**Files:**
- Modify: `backend/app/models/orm.py`

- [ ] **Step 1: Agregar `owner_user_id` a Business y el modelo IngestLog**

En `backend/app/models/orm.py`, dentro de la clase `Business` agregar la columna:

```python
class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    rut = Column(String, unique=True, nullable=True)
    city = Column(String, nullable=True)
    type = Column(String, nullable=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: Agregar `ingest_id` a SalesHistory y crear IngestLog**

En la clase `SalesHistory` agregar:

```python
    ingest_id = Column(Integer, ForeignKey("ingest_log.id"), nullable=True, index=True)
```

Y agregar al final del archivo una clase nueva (importar `JSON` desde sqlalchemy en la primera linea: `from sqlalchemy import ... , JSON`):

```python
class IngestLog(Base):
    __tablename__ = "ingest_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    store_nbr = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # image | excel | pdf
    records_loaded = Column(Integer, nullable=False, default=0)
    sales_unit = Column(String(10), nullable=False, default="units")
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    families = Column(JSON)
    status = Column(String(10), nullable=False, default="active")  # active | reverted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 3: Verificar que la app levanta sin errores de modelo**

```bash
source venv/bin/activate && cd backend && python3.11 -c "from app.models.orm import IngestLog, Business, SalesHistory; print('ok', IngestLog.__tablename__)"
```
Esperado: `ok ingest_log`

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/orm.py
git commit -m "feat(s3): modelos ORM IngestLog, owner_user_id y ingest_id"
```

---

### Task 3: Backfill de datos existentes

**Files:**
- Create: `backend/scripts/backfill_s3_ingest_log.py`

- [ ] **Step 1: Escribir el script de backfill**

```python
# backend/scripts/backfill_s3_ingest_log.py
"""
Crea un ingest_log sintetico ('carga historica') por cada (business_id, store_nbr)
existente en sales_history y asocia sus filas. Asigna owner_user_id a los negocios
que no lo tengan, usando el primer usuario con ese business_id.
Idempotente: salta filas que ya tienen ingest_id.
Uso: source venv/bin/activate && python3.11 backend/scripts/backfill_s3_ingest_log.py
"""
import os, sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from dotenv import load_dotenv
load_dotenv(ROOT / "backend" / ".env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
Session = sessionmaker(bind=engine)

with Session() as db:
    # 1) owner_user_id para negocios sin owner
    db.execute(text("""
        UPDATE businesses b
        SET owner_user_id = (
            SELECT u.id FROM users u WHERE u.business_id = b.id ORDER BY u.id LIMIT 1
        )
        WHERE b.owner_user_id IS NULL
    """))

    # 2) grupos sin ingest_id
    groups = db.execute(text("""
        SELECT business_id, store_nbr,
               MIN(date) AS d0, MAX(date) AS d1,
               COUNT(*) AS n
        FROM sales_history
        WHERE ingest_id IS NULL
        GROUP BY business_id, store_nbr
    """)).fetchall()

    for g in groups:
        user_row = db.execute(text(
            "SELECT COALESCE(owner_user_id, 1) FROM businesses WHERE id = :b"
        ), {"b": g.business_id}).first()
        user_id = user_row[0] if user_row else 1

        fams = db.execute(text("""
            SELECT DISTINCT family FROM sales_history
            WHERE business_id = :b AND store_nbr = :s AND ingest_id IS NULL
        """), {"b": g.business_id, "s": g.store_nbr}).fetchall()
        families = [r[0] for r in fams]

        log_id = db.execute(text("""
            INSERT INTO ingest_log
              (business_id, store_nbr, user_id, filename, file_type,
               records_loaded, sales_unit, date_range_start, date_range_end, families, status)
            VALUES
              (:b, :s, :u, 'carga historica', 'historic',
               :n, 'units', :d0, :d1, CAST(:fam AS JSONB), 'active')
            RETURNING id
        """), {
            "b": g.business_id, "s": g.store_nbr, "u": user_id, "n": g.n,
            "d0": g.d0, "d1": g.d1,
            "fam": __import__("json").dumps(families),
        }).scalar()

        db.execute(text("""
            UPDATE sales_history SET ingest_id = :log
            WHERE business_id = :b AND store_nbr = :s AND ingest_id IS NULL
        """), {"log": log_id, "b": g.business_id, "s": g.store_nbr})

        print(f"business {g.business_id} store {g.store_nbr}: ingest_log {log_id}, {g.n} filas")

    db.commit()
    print("backfill completo")
```

- [ ] **Step 2: Correr el backfill**

```bash
source venv/bin/activate && python3.11 backend/scripts/backfill_s3_ingest_log.py
```
Esperado: una linea por cada `(business, store)` y `backfill completo`.

- [ ] **Step 3: Verificar que no quedan filas sin ingest_id**

```sql
SELECT COUNT(*) FROM sales_history WHERE ingest_id IS NULL;
```
Esperado: `0`

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/backfill_s3_ingest_log.py
git commit -m "feat(s3): backfill de ingest_log para datos historicos"
```

---

## FASE 2 - Schemas y endpoints de backend

### Task 4: Schemas Pydantic nuevos

**Files:**
- Modify: `backend/app/models/schemas.py`

- [ ] **Step 1: Agregar campo owner y schemas de cargas/edicion**

En `BusinessCreate` no cambia nada. En `BusinessResponse` agregar `owner_user_id`:

```python
class BusinessResponse(BaseModel):
    id: int
    name: str
    rut: Optional[str] = None
    city: Optional[str] = None
    type: Optional[str] = None
    owner_user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
```

Agregar al final del bloque "Ingesta IA" (`IngestConfirm` cambia, ver Task 7) estos schemas nuevos:

```python
# ─── Cargas (ingest_log) ────────────────────────────────────────────────────────

class IngestLogResponse(BaseModel):
    id: int
    business_id: int
    store_nbr: int
    user_id: int
    uploader_name: Optional[str] = None
    filename: str
    file_type: str
    records_loaded: int
    sales_unit: str
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    families: Optional[list[str]] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SalesRecordResponse(BaseModel):
    id: int
    date: date
    family: str
    sales: float
    onpromotion: int
    sales_unit: str
    ingest_id: Optional[int] = None

    class Config:
        from_attributes = True


class SalesRecordUpdate(BaseModel):
    date: Optional[date] = None
    family: Optional[str] = None
    sales: Optional[float] = Field(None, ge=0)
    onpromotion: Optional[int] = Field(None, ge=0)
```

- [ ] **Step 2: Verificar import**

```bash
source venv/bin/activate && cd backend && python3.11 -c "from app.models.schemas import IngestLogResponse, SalesRecordResponse, SalesRecordUpdate; print('ok')"
```
Esperado: `ok`

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/schemas.py
git commit -m "feat(s3): schemas IngestLogResponse, SalesRecordResponse, SalesRecordUpdate"
```

---

### Task 5: Endpoint de negocios scoped por usuario

**Files:**
- Modify: `backend/app/api/businesses.py`

- [ ] **Step 1: Filtrar negocios por owner y setear owner al crear**

Reemplazar el contenido de `backend/app/api/businesses.py` por:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import Business, Store, User
from app.models.schemas import BusinessCreate, BusinessResponse, StoreResponse

router = APIRouter()


@router.get("", response_model=list[BusinessResponse])
def list_businesses(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Lista los negocios que pertenecen al usuario actual."""
    return (
        db.query(Business)
        .filter(Business.owner_user_id == current_user.id)
        .order_by(Business.id)
        .all()
    )


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(
    business_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail=f"Negocio {business_id} no encontrado")
    if biz.owner_user_id not in (None, current_user.id):
        raise HTTPException(status_code=403, detail="Este negocio no te pertenece")
    return biz


@router.post("", response_model=BusinessResponse, status_code=201)
def create_business(
    body: BusinessCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Crea un negocio y lo asocia al usuario actual como owner."""
    if body.rut:
        existing = db.query(Business).filter(Business.rut == body.rut).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Ya existe un negocio con RUT {body.rut}")

    biz = Business(
        name=body.name, rut=body.rut, city=body.city, type=body.type,
        owner_user_id=current_user.id,
    )
    db.add(biz)
    db.commit()
    db.refresh(biz)
    return biz


@router.get("/{business_id}/stores", response_model=list[StoreResponse])
def list_business_stores(
    business_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Ubicaciones (tiendas) de un negocio."""
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail=f"Negocio {business_id} no encontrado")
    if biz.owner_user_id not in (None, current_user.id):
        raise HTTPException(status_code=403, detail="Este negocio no te pertenece")
    return (
        db.query(Store)
        .filter(Store.business_id == business_id)
        .order_by(Store.store_nbr)
        .all()
    )
```

- [ ] **Step 2: Verificar el endpoint**

```bash
# con $TOKEN ya seteado (ver header del plan)
curl -s localhost:8000/api/businesses -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```
Esperado: lista JSON de negocios cuyo `owner_user_id` es el del usuario logueado (tras backfill, los negocios del usuario aparecen).

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/businesses.py
git commit -m "feat(s3): negocios scoped por owner + endpoint de ubicaciones"
```

---

### Task 6: Router de cargas (ingest_log)

**Files:**
- Create: `backend/app/api/ingests.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Crear el router de cargas**

```python
# backend/app/api/ingests.py
"""
Gestion de cargas (ingest_log): listar, ver detalle, revertir y eliminar.
Cada carga agrupa las filas de sales_history que se insertaron juntas.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import Business, IngestLog, SalesHistory, User
from app.models.schemas import IngestLogResponse, SalesRecordResponse

router = APIRouter()


def _assert_owner(db: Session, business_id: int, user: User):
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail=f"Negocio {business_id} no encontrado")
    if biz.owner_user_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Este negocio no te pertenece")


@router.get("", response_model=list[IngestLogResponse])
def list_ingests(
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: int = Query(...),
    store_nbr: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Lista las cargas de un negocio (opcionalmente filtradas por ubicacion)."""
    _assert_owner(db, business_id, current_user)
    q = db.query(IngestLog).filter(IngestLog.business_id == business_id)
    if store_nbr is not None:
        q = q.filter(IngestLog.store_nbr == store_nbr)
    logs = q.order_by(IngestLog.created_at.desc()).all()

    names = {u.id: u.name for u in db.query(User).all()}
    out = []
    for log in logs:
        item = IngestLogResponse.model_validate(log)
        item.uploader_name = names.get(log.user_id)
        out.append(item)
    return out


@router.get("/{ingest_id}", response_model=list[SalesRecordResponse])
def get_ingest_records(
    ingest_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Devuelve las filas de sales_history que vinieron de esta carga."""
    log = db.query(IngestLog).filter(IngestLog.id == ingest_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=f"Carga {ingest_id} no encontrada")
    _assert_owner(db, log.business_id, current_user)
    return (
        db.query(SalesHistory)
        .filter(SalesHistory.ingest_id == ingest_id)
        .order_by(SalesHistory.date, SalesHistory.family)
        .all()
    )


@router.post("/{ingest_id}/revert", response_model=IngestLogResponse)
def revert_ingest(
    ingest_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Marca la carga como 'reverted'. Las filas quedan pero salen del calculo."""
    log = db.query(IngestLog).filter(IngestLog.id == ingest_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=f"Carga {ingest_id} no encontrada")
    _assert_owner(db, log.business_id, current_user)
    log.status = "reverted"
    db.commit()
    db.refresh(log)
    item = IngestLogResponse.model_validate(log)
    item.uploader_name = (db.query(User).filter(User.id == log.user_id).first() or User()).name
    return item


@router.delete("/{ingest_id}", status_code=204)
def delete_ingest(
    ingest_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Elimina la carga y todas sus filas de sales_history (hard delete)."""
    log = db.query(IngestLog).filter(IngestLog.id == ingest_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=f"Carga {ingest_id} no encontrada")
    _assert_owner(db, log.business_id, current_user)
    db.query(SalesHistory).filter(SalesHistory.ingest_id == ingest_id).delete()
    db.delete(log)
    db.commit()
```

- [ ] **Step 2: Registrar el router en main.py**

En `backend/app/main.py`, agregar `ingests` al import:

```python
from app.api import auth, forecast, inventory, products, orders, sales, ingest, ingests, businesses, dashboard
```

Y registrar el router junto a los demas:

```python
app.include_router(ingests.router,    prefix="/api/ingests",    tags=["Cargas"],             dependencies=_auth)
```

- [ ] **Step 3: Verificar listado y detalle**

```bash
curl -s "localhost:8000/api/ingests?business_id=18" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```
Esperado: al menos la carga sintetica `carga historica` del negocio 18 (creada en el backfill). Tomar un `id` y:
```bash
curl -s localhost:8000/api/ingests/<ID> -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```
Esperado: lista de registros con `date`, `family`, `sales`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/ingests.py backend/app/main.py
git commit -m "feat(s3): router de cargas (listar/detalle/revertir/eliminar)"
```

---

### Task 7: Confirm de ingesta crea ingest_log

**Files:**
- Modify: `backend/app/api/ingest.py`
- Modify: `backend/app/models/schemas.py`

- [ ] **Step 1: Extender IngestConfirm con metadata de la carga**

En `backend/app/models/schemas.py`, reemplazar `IngestConfirm`:

```python
class IngestConfirm(BaseModel):
    business_id: int
    store_nbr: int
    records: list[IngestRecord]
    sales_unit: Literal["CLP", "units"] = "units"
    filename: str = "carga sin nombre"
    file_type: Literal["image", "excel", "pdf", "historic"] = "excel"
```

- [ ] **Step 2: Reescribir confirm_ingest para crear la carga e insertar con ingest_id**

En `backend/app/api/ingest.py`, reemplazar el cuerpo de `confirm_ingest`. Agregar `User`, `IngestLog`, `get_current_user` a los imports del archivo, y `Annotated` de typing. El nuevo handler:

```python
@router.post("/confirm", response_model=IngestResponse)
def confirm_ingest(
    body: IngestConfirm,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Paso 2: confirma la carga. Crea un ingest_log y agrega las filas con ese
    ingest_id SIN sobrescribir cargas previas (cada carga queda separada).
    """
    if not body.records:
        raise HTTPException(status_code=400, detail="No hay registros para cargar.")

    loadable = filter_loadable_records(body.records)
    if not loadable:
        raise HTTPException(
            status_code=400,
            detail="Ningun registro es cargable (fechas futuras o ventas en cero).",
        )

    dates = [r.date for r in loadable]
    families = sorted(set(r.family for r in loadable))

    log = IngestLog(
        business_id=body.business_id,
        store_nbr=body.store_nbr,
        user_id=current_user.id,
        filename=body.filename,
        file_type=body.file_type,
        records_loaded=len(loadable),
        sales_unit=body.sales_unit,
        date_range_start=min(dates),
        date_range_end=max(dates),
        families=families,
        status="active",
    )
    db.add(log)
    db.flush()  # asigna log.id sin cerrar la transaccion

    for record in loadable:
        db.add(SalesHistory(
            business_id=body.business_id,
            store_nbr=body.store_nbr,
            date=record.date,
            family=record.family,
            sales=record.sales,
            onpromotion=record.onpromotion,
            sales_unit=body.sales_unit,
            ingest_id=log.id,
        ))

    for family in families:
        exists = db.query(Product).filter(
            Product.business_id == body.business_id,
            Product.family == family,
            Product.store_nbr == body.store_nbr,
        ).first()
        if not exists:
            db.add(Product(
                business_id=body.business_id,
                sku_id=family,
                name=family.title(),
                family=family,
                store_nbr=body.store_nbr,
                unit_cost=0.0,
            ))

    db.commit()

    return IngestResponse(
        store_nbr=body.store_nbr,
        records_loaded=len(loadable),
        families=families,
        date_range_start=min(dates),
        date_range_end=max(dates),
    )
```

Imports a asegurar al tope de `ingest.py`:
```python
from typing import Annotated
from app.api.auth import get_current_user
from app.models.orm import Business, Product, SalesHistory, User, IngestLog
```

- [ ] **Step 3: Verificar carga end-to-end via /docs**

Arrancar uvicorn, ir a `http://localhost:8000/docs`, autorizar con el token. Ejecutar `POST /api/ingest/confirm` con body:
```json
{"business_id": 18, "store_nbr": 1, "sales_unit": "units", "filename": "prueba.xlsx", "file_type": "excel",
 "records": [{"date":"2025-12-01","family":"PRUEBA","sales":10,"onpromotion":0}]}
```
Esperado: 200 con `records_loaded: 1`. Luego `GET /api/ingests?business_id=18` debe mostrar la carga nueva "prueba.xlsx".

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/ingest.py backend/app/models/schemas.py
git commit -m "feat(s3): confirm de ingesta crea ingest_log y no sobrescribe"
```

---

### Task 8: Edicion y borrado de registros individuales

**Files:**
- Modify: `backend/app/api/sales.py`

- [ ] **Step 1: Agregar PATCH y DELETE de registros**

En `backend/app/api/sales.py`, agregar los imports de auth y schemas, y dos endpoints nuevos al final:

```python
from typing import Annotated
from app.api.auth import get_current_user
from app.models.orm import Business, User
from app.models.schemas import SalesRecordResponse, SalesRecordUpdate


def _assert_record_owner(db: Session, record: SalesHistory, user: User):
    biz = db.query(Business).filter(Business.id == record.business_id).first()
    if biz and biz.owner_user_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Este registro no te pertenece")


@router.patch("/record/{record_id}", response_model=SalesRecordResponse)
def update_record(
    record_id: int,
    body: SalesRecordUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Edita una fila de sales_history (venta, fecha, familia, promo)."""
    rec = db.query(SalesHistory).filter(SalesHistory.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Registro {record_id} no encontrado")
    _assert_record_owner(db, rec, current_user)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rec, field, value)
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/record/{record_id}", status_code=204)
def delete_record(
    record_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Elimina una fila individual de sales_history."""
    rec = db.query(SalesHistory).filter(SalesHistory.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Registro {record_id} no encontrado")
    _assert_record_owner(db, rec, current_user)
    db.delete(rec)
    db.commit()
```

- [ ] **Step 2: Verificar edicion**

Tomar el `id` de un registro via `GET /api/ingests/<ID>` (lista filas con su `id`). Luego:
```bash
curl -s -X PATCH localhost:8000/api/sales/record/<REC_ID> \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"sales": 99}' | python3 -m json.tool
```
Esperado: 200 con `sales: 99.0`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/sales.py
git commit -m "feat(s3): PATCH/DELETE de registros individuales de sales_history"
```

---

### Task 9: Vista de combinacion (ultima gana + solo activas) en forecast

**Files:**
- Modify: `backend/app/services/forecast_service.py:59-90`

- [ ] **Step 1: Filtrar por cargas activas y resolver solape "ultima gana"**

En `_load_series_from_db`, la query debe (1) unir con `ingest_log` para excluir cargas `reverted`, y (2) cuando hay varias filas para el mismo `date`, quedarse con la de la carga mas reciente. Reemplazar la query por:

```python
def _load_series_from_db(
    db: Session,
    business_id: int,
    sku_id: str,
    store_nbr: int,
) -> pd.Series:
    """
    Serie diaria desde sales_history scoped por business_id + store_nbr.
    Solo cuenta cargas activas (ingest_log.status='active'). Si dos cargas
    activas cubren el mismo dia, gana la de mayor ingest_id (mas reciente).
    """
    from sqlalchemy import text
    rows = db.execute(text("""
        SELECT s.date, s.sales
        FROM sales_history s
        JOIN ingest_log il ON il.id = s.ingest_id
        WHERE s.business_id = :b
          AND s.family = :fam
          AND s.store_nbr = :store
          AND s.date <= CURRENT_DATE
          AND il.status = 'active'
          AND s.ingest_id = (
              SELECT s2.ingest_id
              FROM sales_history s2
              JOIN ingest_log il2 ON il2.id = s2.ingest_id
              WHERE s2.business_id = s.business_id
                AND s2.family = s.family
                AND s2.store_nbr = s.store_nbr
                AND s2.date = s.date
                AND il2.status = 'active'
              ORDER BY s2.ingest_id DESC
              LIMIT 1
          )
        ORDER BY s.date
    """), {"b": business_id, "fam": sku_id, "store": store_nbr}).fetchall()

    if not rows:
        return pd.Series(dtype=float)
    s = pd.Series(
        [r[1] for r in rows],
        index=pd.to_datetime([r[0] for r in rows]),
    )
    return s.asfreq("D").interpolate()
```

Nota: si la version actual de la funcion construye la serie de otra forma (revisar `:59-90`), preservar el post-procesamiento existente (asfreq/interpolate) y reemplazar solo la obtencion de filas. La clave es el JOIN con `ingest_log` y el subselect "ultima gana".

- [ ] **Step 2: Verificar que el forecast sigue corriendo sobre data real**

Con uvicorn arriba, en `/docs` ejecutar `POST /api/forecast` con un SKU/familia real del negocio 18 (ej. `PANADERIA Y PASTELERIA`, store 1, horizon 7). Esperado: 200 con `predictions` no vacias y `model_used` definido. Revertir una carga (`POST /api/ingests/<id>/revert`) de ese negocio y re-ejecutar: la serie debe excluir esas filas.

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/forecast_service.py
git commit -m "feat(s3): forecast lee solo cargas activas con resolucion ultima-gana"
```

---

## FASE 3 - Frontend: pagina Datos y selector de destino

### Task 10: Cliente API de negocios y cargas

**Files:**
- Create: `frontend/src/api/data.ts`

- [ ] **Step 1: Crear el modulo de API**

```typescript
// frontend/src/api/data.ts
import api from "./axios.instance";

export interface Business {
  id: number;
  name: string;
  rut: string | null;
  city: string | null;
  type: string | null;
  owner_user_id: number | null;
  created_at: string;
}

export interface StoreItem {
  store_nbr: number;
  city: string | null;
  state: string | null;
  type: string | null;
  cluster: number | null;
}

export interface IngestLogItem {
  id: number;
  business_id: number;
  store_nbr: number;
  user_id: number;
  uploader_name: string | null;
  filename: string;
  file_type: string;
  records_loaded: number;
  sales_unit: string;
  date_range_start: string | null;
  date_range_end: string | null;
  families: string[] | null;
  status: string;
  created_at: string;
}

export interface SalesRecord {
  id: number;
  date: string;
  family: string;
  sales: number;
  onpromotion: number;
  sales_unit: string;
  ingest_id: number | null;
}

export async function listBusinesses(): Promise<Business[]> {
  const { data } = await api.get("/businesses");
  return data;
}

export async function createBusiness(payload: {
  name: string; rut?: string; city?: string; type?: string;
}): Promise<Business> {
  const { data } = await api.post("/businesses", payload);
  return data;
}

export async function listBusinessStores(businessId: number): Promise<StoreItem[]> {
  const { data } = await api.get(`/businesses/${businessId}/stores`);
  return data;
}

export async function listIngests(businessId: number, storeNbr?: number): Promise<IngestLogItem[]> {
  const params: Record<string, number> = { business_id: businessId };
  if (storeNbr != null) params.store_nbr = storeNbr;
  const { data } = await api.get("/ingests", { params });
  return data;
}

export async function getIngestRecords(ingestId: number): Promise<SalesRecord[]> {
  const { data } = await api.get(`/ingests/${ingestId}`);
  return data;
}

export async function revertIngest(ingestId: number): Promise<IngestLogItem> {
  const { data } = await api.post(`/ingests/${ingestId}/revert`);
  return data;
}

export async function deleteIngest(ingestId: number): Promise<void> {
  await api.delete(`/ingests/${ingestId}`);
}

export async function updateRecord(
  recordId: number,
  patch: Partial<Pick<SalesRecord, "date" | "family" | "sales" | "onpromotion">>,
): Promise<SalesRecord> {
  const { data } = await api.patch(`/sales/record/${recordId}`, patch);
  return data;
}

export async function deleteRecord(recordId: number): Promise<void> {
  await api.delete(`/sales/record/${recordId}`);
}
```

- [ ] **Step 2: Verificar que compila**

```bash
cd frontend && npx tsc --noEmit
```
Esperado: sin errores nuevos en `data.ts`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/data.ts
git commit -m "feat(s3): cliente API de negocios y cargas"
```

---

### Task 11: Pagina Datos (drill-down negocio -> ubicacion -> cargas)

**Files:**
- Create: `frontend/src/pages/Datos.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Crear la pagina Datos**

```tsx
// frontend/src/pages/Datos.tsx
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Database, ChevronDown, ChevronRight, RotateCcw, Trash2, Loader2 } from "lucide-react";
import {
  listBusinesses, listBusinessStores, listIngests, getIngestRecords,
  revertIngest, deleteIngest,
} from "../api/data";

export default function Datos() {
  const qc = useQueryClient();
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [storeNbr, setStoreNbr] = useState<number | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  const businesses = useQuery({ queryKey: ["businesses"], queryFn: listBusinesses });

  const stores = useQuery({
    queryKey: ["stores", businessId],
    queryFn: () => listBusinessStores(businessId!),
    enabled: businessId != null,
  });

  const ingests = useQuery({
    queryKey: ["ingests", businessId, storeNbr],
    queryFn: () => listIngests(businessId!, storeNbr ?? undefined),
    enabled: businessId != null,
  });

  const revertMut = useMutation({
    mutationFn: (id: number) => revertIngest(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ingests"] }),
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteIngest(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ingests"] }),
  });

  return (
    <div className="p-6 space-y-6">
      <header className="flex items-center gap-2">
        <Database className="w-6 h-6 text-indigo-600" />
        <h1 className="text-2xl font-bold">Datos</h1>
      </header>

      {/* Selector de negocio */}
      <div className="flex flex-wrap gap-3 items-center">
        <select
          className="border rounded-lg px-3 py-2"
          value={businessId ?? ""}
          onChange={(e) => { setBusinessId(Number(e.target.value) || null); setStoreNbr(null); }}
        >
          <option value="">Selecciona un negocio</option>
          {businesses.data?.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>

        {businessId != null && (
          <select
            className="border rounded-lg px-3 py-2"
            value={storeNbr ?? ""}
            onChange={(e) => setStoreNbr(e.target.value === "" ? null : Number(e.target.value))}
          >
            <option value="">Todas las ubicaciones</option>
            {stores.data?.map((s) => (
              <option key={s.store_nbr} value={s.store_nbr}>
                Ubicacion {s.store_nbr}{s.city ? ` - ${s.city}` : ""}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Tabla de cargas */}
      {businessId == null ? (
        <p className="text-gray-500">Elige un negocio para ver sus cargas.</p>
      ) : ingests.isLoading ? (
        <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
      ) : ingests.data?.length === 0 ? (
        <p className="text-gray-500">Este negocio no tiene cargas aun.</p>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="px-3 py-2 w-8"></th>
                <th className="px-3 py-2">Fecha</th>
                <th className="px-3 py-2">Archivo</th>
                <th className="px-3 py-2">Quien</th>
                <th className="px-3 py-2">Filas</th>
                <th className="px-3 py-2">Rango</th>
                <th className="px-3 py-2">Unidad</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {ingests.data?.map((log) => (
                <RowGroup
                  key={log.id}
                  log={log}
                  open={expanded === log.id}
                  onToggle={() => setExpanded(expanded === log.id ? null : log.id)}
                  onRevert={() => revertMut.mutate(log.id)}
                  onDelete={() => {
                    if (confirm(`Eliminar la carga "${log.filename}" y sus ${log.records_loaded} filas?`))
                      deleteMut.mutate(log.id);
                  }}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function RowGroup({ log, open, onToggle, onRevert, onDelete }: {
  log: import("../api/data").IngestLogItem;
  open: boolean;
  onToggle: () => void;
  onRevert: () => void;
  onDelete: () => void;
}) {
  const records = useQuery({
    queryKey: ["ingest-records", log.id],
    queryFn: () => getIngestRecords(log.id),
    enabled: open,
  });

  return (
    <>
      <tr className="border-t hover:bg-gray-50">
        <td className="px-3 py-2">
          <button onClick={onToggle}>
            {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        </td>
        <td className="px-3 py-2">{new Date(log.created_at).toLocaleDateString("es-CL")}</td>
        <td className="px-3 py-2">{log.filename}</td>
        <td className="px-3 py-2">{log.uploader_name ?? "-"}</td>
        <td className="px-3 py-2">{log.records_loaded}</td>
        <td className="px-3 py-2">{log.date_range_start} -> {log.date_range_end}</td>
        <td className="px-3 py-2">{log.sales_unit}</td>
        <td className="px-3 py-2">
          <span className={log.status === "active" ? "text-green-600" : "text-gray-400"}>
            {log.status === "active" ? "activa" : "revertida"}
          </span>
        </td>
        <td className="px-3 py-2 flex gap-2">
          {log.status === "active" && (
            <button onClick={onRevert} title="Revertir" className="text-amber-600">
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
          <button onClick={onDelete} title="Eliminar" className="text-red-600">
            <Trash2 className="w-4 h-4" />
          </button>
        </td>
      </tr>
      {open && (
        <tr>
          <td colSpan={9} className="bg-gray-50 px-6 py-3">
            {records.isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <table className="w-full text-xs">
                <thead className="text-left text-gray-500">
                  <tr><th className="py-1">Fecha</th><th>Familia</th><th>Venta</th><th>Promo</th></tr>
                </thead>
                <tbody>
                  {records.data?.map((r) => (
                    <tr key={r.id} className="border-t">
                      <td className="py-1">{r.date}</td>
                      <td>{r.family}</td>
                      <td>{r.sales}</td>
                      <td>{r.onpromotion}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
```

- [ ] **Step 2: Registrar la ruta en App.tsx**

En `frontend/src/App.tsx`, importar `Datos` y agregar la ruta protegida junto a las demas (mismo patron que `Ingest`):

```tsx
import Datos from "./pages/Datos";
// ...dentro de las rutas protegidas:
<Route path="/datos" element={<Datos />} />
```

- [ ] **Step 3: Agregar el link en el Sidebar**

En `frontend/src/components/layout/Sidebar.tsx`, agregar un item de navegacion "Datos" (icono `Database` de lucide-react) que apunte a `/datos`, siguiendo el patron del item de "Ingesta" existente.

- [ ] **Step 4: Verificar en el navegador**

```bash
cd frontend && npm run dev
```
Abrir `http://localhost:5173/datos`. Esperado: selector de negocios poblado; al elegir negocio 18 aparece la tabla de cargas; expandir una carga muestra sus registros; el boton revertir cambia el estado a "revertida"; eliminar pide confirmacion.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Datos.tsx frontend/src/App.tsx frontend/src/components/layout/Sidebar.tsx
git commit -m "feat(s3): pagina Datos con drill-down negocio/ubicacion/cargas"
```

---

### Task 12: Edicion inline de registros en la pagina Datos

**Files:**
- Modify: `frontend/src/pages/Datos.tsx`

- [ ] **Step 1: Agregar edicion y borrado de filas en el detalle**

En `Datos.tsx`, dentro de `RowGroup`, importar `updateRecord` y `deleteRecord` de `../api/data` y `useMutation`/`useQueryClient`. Convertir la tabla de registros para que cada celda de `sales` sea editable: al hacer doble click se vuelve un `<input type="number">` que al `onBlur` llama `updateRecord(r.id, { sales: nuevoValor })` e invalida `["ingest-records", log.id]`. Agregar una columna de accion con un boton borrar que llame `deleteRecord(r.id)` (con `confirm`) e invalide la misma query. Codigo del bloque de mutaciones a agregar dentro de `RowGroup`:

```tsx
  const qc = useQueryClient();
  const editMut = useMutation({
    mutationFn: ({ id, sales }: { id: number; sales: number }) => updateRecord(id, { sales }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ingest-records", log.id] }),
  });
  const delRecMut = useMutation({
    mutationFn: (id: number) => deleteRecord(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ingest-records", log.id] }),
  });
```

Y la celda editable de venta:
```tsx
<td>
  <input
    type="number"
    defaultValue={r.sales}
    className="w-24 border rounded px-1"
    onBlur={(e) => {
      const v = Number(e.target.value);
      if (v !== r.sales) editMut.mutate({ id: r.id, sales: v });
    }}
  />
</td>
<td>
  <button className="text-red-500" onClick={() => {
    if (confirm("Eliminar este registro?")) delRecMut.mutate(r.id);
  }}>
    <Trash2 className="w-3 h-3" />
  </button>
</td>
```
Agregar tambien las cabeceras de columna correspondientes (`Venta` ya existe, agregar columna vacia para la accion).

- [ ] **Step 2: Verificar en el navegador**

En `/datos`, expandir una carga, cambiar un valor de venta y salir del input: el valor debe persistir tras refrescar. Borrar una fila: debe desaparecer y bajar el conteo al recargar la carga.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Datos.tsx
git commit -m "feat(s3): edicion y borrado inline de registros en pagina Datos"
```

---

### Task 13: Selector de destino en el flujo de ingesta

**Files:**
- Modify: `frontend/src/api/ingest.ts`
- Modify: `frontend/src/store/ingestStore.ts`
- Modify: `frontend/src/pages/Ingest.tsx`

- [ ] **Step 1: Pasar metadata de la carga en confirmIngest**

En `frontend/src/api/ingest.ts`, extender `confirmIngest`:

```typescript
export async function confirmIngest(
  records: IngestRecord[],
  store_nbr: number,
  business_id: number,
  sales_unit: "CLP" | "units" = "units",
  filename: string = "carga sin nombre",
  file_type: "image" | "excel" | "pdf" = "excel",
): Promise<IngestResponse> {
  const { data } = await api.post("/ingest/confirm", {
    records, store_nbr, business_id, sales_unit, filename, file_type,
  });
  return data;
}
```

- [ ] **Step 2: Guardar negocio destino en el store**

En `frontend/src/store/ingestStore.ts`, agregar `businessId: number | null` con su setter y en `initialState` (`businessId: null`). Patron identico a `storeNbr`.

- [ ] **Step 3: Agregar el selector de destino en el paso preview**

En `frontend/src/pages/Ingest.tsx`, en el paso `preview` (antes del boton Confirmar), agregar un bloque que use `listBusinesses` y `listBusinessStores` (de `../api/data`, via `useQuery`) para elegir negocio y ubicacion destino. Si `businessId` del store es null, prefijar con `user?.business_id`. Pasar `businessId` y `storeNbr` elegidos a `confirmMut`. Actualizar `confirmMut`:

```tsx
const confirmMut = useMutation({
  mutationFn: () => confirmIngest(
    preview!.records,
    storeNbr,
    businessId ?? user?.business_id ?? 1,
    salesUnit ?? "units",
    fileName,
    inferFileType(fileName),
  ),
  onSuccess: (data) => {
    setSuccessData({ loaded: data.records_loaded, families: data.families, start: data.date_range_start, end: data.date_range_end });
    setStep("success");
  },
});

function inferFileType(name: string): "image" | "excel" | "pdf" {
  const n = name.toLowerCase();
  if (n.endsWith(".pdf")) return "pdf";
  if (/\.(jpe?g|png|webp)$/.test(n)) return "image";
  return "excel";
}
```

Agregar el UI de seleccion (negocio + ubicacion) con un boton "+ Nuevo negocio" que llame `createBusiness` y refresque la lista. El boton Confirmar queda deshabilitado si no hay negocio destino elegido.

- [ ] **Step 4: Verificar el flujo completo**

En `/ingest`, subir un archivo de prueba, en el preview elegir negocio + ubicacion destino, confirmar. Esperado: la carga aparece luego en `/datos` bajo ese negocio/ubicacion con el `filename` real y el usuario actual como "quien".

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/ingest.ts frontend/src/store/ingestStore.ts frontend/src/pages/Ingest.tsx
git commit -m "feat(s3): selector de negocio/ubicacion destino en ingesta"
```

---

## FASE 4 - Asistencia de IA (Stocky ampliado)

### Task 14: Stocky sugiere destino y detecta solape en el preview

**Files:**
- Modify: `backend/app/services/ingest_service.py`
- Modify: `backend/app/api/ingest.py`

- [ ] **Step 1: Pasar cargas existentes al contexto de Stocky en el chat**

En `backend/app/api/ingest.py`, en `ingest_chat`, antes de llamar `service.chat`, consultar las cargas activas del negocio del usuario y construir un resumen corto (nombre de ubicacion, familias, rango) para inyectarlo. Pasar ese resumen como argumento nuevo `existing_loads` a `service.chat`:

```python
    existing = (
        db.query(IngestLog)
        .filter(IngestLog.business_id == current_user.business_id, IngestLog.status == "active")
        .order_by(IngestLog.created_at.desc())
        .limit(10)
        .all()
    )
    loads_summary = "; ".join(
        f"ubicacion {l.store_nbr}: {', '.join(l.families or [])} ({l.date_range_start} a {l.date_range_end})"
        for l in existing
    ) or "ninguna carga previa"
    reply, trigger_confirm = service.chat(body.messages, body.preview_summary, business_name, loads_summary)
```
Agregar `IngestLog` al import de `app.models.orm` en `ingest.py`.

- [ ] **Step 2: Usar el contexto en el prompt de Stocky**

En `backend/app/services/ingest_service.py`, en el metodo `chat`, agregar el parametro `existing_loads: str = ""` y sumarlo al system prompt: una instruccion del tipo "El usuario ya tiene estas cargas previas: {existing_loads}. Si la carga actual se parece a una de ellas (familias o rango de fechas), sugiere el negocio/ubicacion destino. Si las fechas solapan con una carga existente, avisa que la mas reciente prevalecera."

- [ ] **Step 3: Verificar respuesta contextual**

Con uvicorn arriba y un negocio con cargas previas, subir un archivo con familias parecidas. En el chat de Stocky (paso preview) la respuesta deberia mencionar la ubicacion existente similar y/o el solape. Verificar manualmente leyendo la respuesta del chat.

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/ingest_service.py backend/app/api/ingest.py
git commit -m "feat(s3): Stocky sugiere destino y detecta solape de cargas"
```

---

### Task 15: Boton "Preguntar a Stocky" en la pagina Datos

**Files:**
- Modify: `frontend/src/pages/Datos.tsx`

- [ ] **Step 1: Agregar consulta a Stocky sobre una carga**

En `Datos.tsx`, agregar en cada `RowGroup` un boton "Preguntar a Stocky" que arme un `preview_summary` con la metadata de la carga (familias, rango, # filas, estado) y llame `chatIngest([{role:"user", content:"Resume esta carga y dime si tiene huecos o ventas raras"}], summary)` de `../api/ingest`. Mostrar la respuesta en un panel desplegable bajo la carga. Reusar el componente de markdown (`ReactMarkdown`) ya presente en el proyecto.

```tsx
  const [stockyReply, setStockyReply] = useState<string | null>(null);
  const askMut = useMutation({
    mutationFn: () => chatIngest(
      [{ role: "user", content: "Resume esta carga y dime si tiene huecos o ventas raras." }],
      `Carga ${log.filename}: familias ${(log.families || []).join(", ")}, rango ${log.date_range_start} a ${log.date_range_end}, ${log.records_loaded} filas, estado ${log.status}.`,
    ),
    onSuccess: (res) => setStockyReply(res.reply),
  });
```
Y el boton + panel:
```tsx
<button onClick={() => askMut.mutate()} className="text-indigo-600 text-xs">Preguntar a Stocky</button>
{stockyReply && (
  <div className="mt-2 p-3 bg-indigo-50 rounded text-xs">
    <ReactMarkdown>{stockyReply}</ReactMarkdown>
  </div>
)}
```

- [ ] **Step 2: Verificar en el navegador**

En `/datos`, expandir una carga y pulsar "Preguntar a Stocky". Esperado: aparece un resumen en lenguaje natural de la carga.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Datos.tsx
git commit -m "feat(s3): boton Preguntar a Stocky en pagina Datos"
```

---

## Verificacion final (end-to-end)

- [ ] Aplicar migracion + backfill en Supabase (Tasks 1, 3 ya corridos).
- [ ] Crear un negocio nuevo desde el front, ingestar un archivo eligiendo ese negocio como destino.
- [ ] Ver la carga en `/datos`, expandir, editar una venta, revertir la carga, comprobar que el forecast del negocio ya no la usa.
- [ ] Eliminar una carga y confirmar que sus filas desaparecen de `sales_history`.
- [ ] Confirmar que un usuario solo ve sus propios negocios (`GET /api/businesses`).

## Actualizar CLAUDE.md

- [ ] Agregar al estado actual de `CLAUDE.md` la seccion "Sprint 3 - gestion de datos y cargas" describiendo `ingest_log`, el cambio de UPSERT a cargas separadas, la resolucion ultima-gana, la pagina Datos y Stocky ampliado. Quitar de "Pendiente" el item S3 de refinamiento de ingesta.
