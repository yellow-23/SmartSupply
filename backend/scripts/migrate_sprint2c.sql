-- ============================================================
-- SmartSupply — Migración Sprint 2-C
-- Ejecutar en Supabase SQL Editor (dashboard.supabase.com)
-- ============================================================

-- Crear tabla si no existe (instalación limpia)
CREATE TABLE IF NOT EXISTS public.products (
    id               SERIAL PRIMARY KEY,
    sku_id           TEXT NOT NULL UNIQUE,
    name             TEXT NOT NULL,
    family           TEXT NOT NULL,
    store_nbr        INTEGER NOT NULL DEFAULT 1,
    unit_cost        FLOAT8 NOT NULL DEFAULT 0,
    lead_time_days   INTEGER NOT NULL DEFAULT 3,
    order_cost       FLOAT8 NOT NULL DEFAULT 0,
    holding_cost_pct FLOAT8 NOT NULL DEFAULT 0.20,
    min_order_qty    INTEGER NOT NULL DEFAULT 1,
    pack_size        INTEGER NOT NULL DEFAULT 1,
    supplier_name    TEXT,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Agregar columnas que pueden faltar si la tabla ya existía con esquema previo
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS unit_cost        FLOAT8 NOT NULL DEFAULT 0;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS lead_time_days   INTEGER NOT NULL DEFAULT 3;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS order_cost       FLOAT8 NOT NULL DEFAULT 0;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS holding_cost_pct FLOAT8 NOT NULL DEFAULT 0.20;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS min_order_qty    INTEGER NOT NULL DEFAULT 1;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS pack_size        INTEGER NOT NULL DEFAULT 1;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS supplier_name    TEXT;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS is_active        BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS store_nbr        INTEGER NOT NULL DEFAULT 1;
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_products_family     ON public.products (family);
CREATE INDEX IF NOT EXISTS idx_products_store_nbr  ON public.products (store_nbr);
CREATE INDEX IF NOT EXISTS idx_products_is_active  ON public.products (is_active);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_products_updated_at ON public.products;
CREATE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON public.products
    FOR EACH ROW
    EXECUTE FUNCTION public.set_updated_at();
