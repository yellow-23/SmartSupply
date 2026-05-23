-- ============================================================
-- SmartSupply — Migración Inicial
-- Crea las tablas base: businesses y users
-- Ejecutar en Supabase SQL Editor ANTES de las demás migraciones
-- ============================================================

-- ─── Tabla: businesses ───────────────────────────────────────────────────────
-- Cada distribuidora/cliente es un Business independiente.
-- business_id=1 es el negocio demo por defecto.

CREATE TABLE IF NOT EXISTS public.businesses (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    rut        TEXT UNIQUE,
    city       TEXT,
    type       TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Negocio demo para desarrollo (business_id=1 es el default en todos los modelos)
-- type=NULL para evitar el CHECK constraint que puede variar entre instancias
INSERT INTO public.businesses (id, name, rut, city, type)
VALUES (1, 'Distribuidora Demo', NULL, 'Santiago', NULL)
ON CONFLICT (id) DO NOTHING;

-- ─── Tabla: users ────────────────────────────────────────────────────────────
-- Usuarios del sistema. hashed_password usa bcrypt.
-- role: 'admin' | 'analyst'

CREATE TABLE IF NOT EXISTS public.users (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'analyst',
    business_id     INTEGER NOT NULL DEFAULT 1
                        REFERENCES public.businesses(id) ON DELETE RESTRICT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email       ON public.users (email);
CREATE INDEX IF NOT EXISTS idx_users_business_id ON public.users (business_id);

-- ─── Notas ───────────────────────────────────────────────────────────────────
-- Para crear el usuario admin inicial usa el script Python:
--   cd backend && python3.11 scripts/create_user.py
-- o crea el hash con bcrypt y haz INSERT directamente:
--   INSERT INTO public.users (name, email, hashed_password, role, business_id)
--   VALUES ('Admin', 'cristobal@distribuidora.cl', '<bcrypt_hash>', 'admin', 1);
