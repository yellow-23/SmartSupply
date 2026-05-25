# Gestion de datos y cargas (ingest_log) - Diseño

Fecha: 2026-05-24
Autor: Cristobal (Int.3 - backend/etl/frontend)
Estado: aprobado, pendiente de plan de implementacion

## Problema

Hoy toda la data ingestada (imagen, Excel, PDF) cae en una sola tabla `sales_history`
sin traza de origen. No se sabe quien subio que, cuando, ni desde que archivo. Si una
carga trae datos malos no hay forma de identificarla ni revertirla sin SQL directo. Las
cargas se mezclan via UPSERT, destruyendo el valor anterior.

## Objetivo

Modelo de datos auditable y flexible donde:
- Cada registro de venta sabe de que carga vino y quien la subio.
- Un usuario administra varios negocios; cada negocio varias ubicaciones; cada ubicacion
  varias cargas. Jerarquia: Usuario -> Negocios -> Ubicaciones -> Cargas -> Registros.
- Las cargas se mantienen separadas (no se sobrescriben); el solapamiento se resuelve al
  consultar, no al cargar. Los datos crudos quedan intactos y auditables.
- El usuario ve, edita y revierte cargas desde el front, con asistencia de IA (Stocky).
- La experiencia es personalizable: nombres libres de negocios/ubicaciones, modo de
  combinacion por negocio.

## Seccion 1: Modelo de datos

### Cambios en tablas existentes

```
businesses
  + owner_user_id  FK -> users.id     # un negocio pertenece a un usuario

users
  business_id  -> pasa a ser "negocio activo seleccionado" (no fijo).
                  Se mantiene la columna como puntero al negocio en contexto;
                  el listado de negocios del usuario se deriva de
                  businesses.owner_user_id.
```

### Tabla nueva `ingest_log`

```
ingest_log
  id              PK
  business_id     FK -> businesses
  store_nbr       int            # ubicacion destino
  user_id         FK -> users    # quien la subio
  filename        varchar
  file_type       varchar        # image | excel | pdf
  records_loaded  int
  sales_unit      varchar        # CLP | units
  date_range_start  date
  date_range_end    date
  families        json
  status          varchar        # 'active' | 'reverted'
  created_at      timestamp
```

### Cambio en `sales_history`

```
sales_history
  + ingest_id  FK -> ingest_log   # cada fila sabe de que carga vino
```

### Cambio de comportamiento de carga

El confirm ya no hace UPSERT. Cada carga inserta sus filas con su `ingest_id` sin
sobrescribir filas previas. La unicidad pasa de
`UNIQUE (business_id, date, family, store_nbr)` a incluir `ingest_id`:
`UNIQUE (business_id, store_nbr, date, family, ingest_id)`.

## Seccion 2: Combinacion de cargas al consultar

Como dos cargas pueden cubrir el mismo (date, family, store_nbr), el solapamiento se
resuelve en la lectura mediante una vista SQL o en la query de `forecast_service`, nunca
mutando `sales_history`.

| Modo | Comportamiento ante solape (mismo dia+familia+ubicacion) |
|------|------|
| Ultima gana (default) | Usa el valor de la carga mas reciente (`MAX(created_at)`). |
| Sumar (futuro) | Suma los valores. Para consolidar fuentes/sucursales distintas. |
| Solo activas (siempre) | Solo cuenta cargas con `status='active'`. Revertir saca la carga del calculo sin borrar nada. |

Comportamiento base aprobado: **ultima gana + solo activas**. "Sumar" queda como flag
seleccionable por negocio para una iteracion futura.

## Seccion 3: Endpoints del backend

```
# Negocios (multi-negocio por usuario)
GET    /api/businesses                  -> lista negocios del usuario actual
POST   /api/businesses                  -> crear negocio
GET    /api/businesses/{id}/stores      -> ubicaciones de un negocio

# Cargas (ingest_log)
GET    /api/ingests?business_id=&store_nbr=   -> lista de cargas (filtrable)
GET    /api/ingests/{id}                      -> detalle + registros de esa carga
POST   /api/ingests/{id}/revert               -> marca status='reverted'
DELETE /api/ingests/{id}                       -> elimina carga + sus filas (hard delete)

# Edicion de registros
PATCH  /api/sales/{record_id}    -> editar una fila (sales, date, family)
DELETE /api/sales/{record_id}    -> eliminar una fila
```

`POST /api/ingest/confirm` cambia: crea primero un `ingest_log`, luego inserta las filas
con ese `ingest_id`, y recibe `business_id` + `store_nbr` destino (ya no usa el fijo del
usuario). `IngestConfirm` schema gana los campos necesarios.

## Seccion 4: Frontend - pagina "Datos"

Nueva entrada en el sidebar. Navegacion en arbol con drill-down:

```
Negocio (selector arriba)  [+ Nuevo negocio]
 └─ Ubicacion (tabs/selector)  [+ Nueva ubicacion]
     └─ Tabla de cargas:
        fecha | archivo | quien subio | # filas | rango | unidad | estado
        acciones por fila: [ver registros] [revertir] [eliminar]

        Al "ver registros" -> tabla expandible editable inline
        (editar venta, fecha, familia; eliminar fila)
```

El flujo de **Ingesta** gana un paso antes de confirmar: "¿A que negocio y ubicacion va
esta carga?" con opcion de crear negocio/ubicacion nuevos ahi mismo.

## Seccion 5: Asistencia de IA (Stocky ampliado)

Stocky hoy solo vive en el preview de ingesta. Se extiende a la gestion de datos.

En el flujo de ingesta:
- Sugiere automaticamente el negocio/ubicacion destino comparando familias y rango de
  fechas con cargas previas.
- Detecta solape con una carga existente y recomienda el modo de combinacion conveniente.

En la pagina "Datos":
- Boton "Preguntar a Stocky" sobre cualquier carga o ubicacion (huecos, ventas raras,
  resumen de datos del negocio).
- Propone acciones (revertir carga con datos malos, fusionar dos cargas) que el usuario
  confirma con un click.

Personalizacion:
- Modo de combinacion configurable por negocio (ultima gana / sumar).
- Nombres libres de negocios y ubicaciones.
- Stocky recuerda el contexto del negocio activo en sus respuestas.

## Fuera de alcance (por ahora)

- Modo de combinacion "sumar" (solo se deja el flag, no la logica completa).
- Notificaciones por email de cargas.
- Compartir negocios entre varios usuarios (un negocio tiene un solo owner).

## Notas de migracion

- Migracion SQL nueva: `owner_user_id` en businesses, tabla `ingest_log`, `ingest_id`
  en sales_history, cambio de constraint unico.
- Backfill: por cada `(business_id, store_nbr)` existente en `sales_history` se crea un
  `ingest_log` sintetico con `filename='carga historica'`, `status='active'`,
  `user_id` = owner del negocio, y se setea `ingest_id` en sus filas. Asi ninguna fila
  queda con `ingest_id = NULL` y la pagina "Datos" muestra los datos previos como una
  carga mas.
- `businesses` existentes (2, 17, 18) necesitan `owner_user_id` asignado al usuario
  correspondiente.
