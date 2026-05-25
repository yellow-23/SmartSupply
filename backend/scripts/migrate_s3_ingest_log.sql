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
-- Constraint vieja real en esta DB: sales_history_unique_record
ALTER TABLE sales_history DROP CONSTRAINT IF EXISTS sales_history_unique_record;
ALTER TABLE sales_history
  ADD CONSTRAINT uq_sales_history_load
  UNIQUE (business_id, store_nbr, date, family, ingest_id);
