-- ============================================================
-- SmartSupply — Migración Sprint 2
-- Ejecutar en Supabase SQL Editor (dashboard.supabase.com)
-- ============================================================

-- Tabla: password_reset_tokens
-- Almacena tokens de recuperación de contraseña con TTL 30 min
CREATE TABLE IF NOT EXISTS public.password_reset_tokens (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    token       TEXT    NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prt_token   ON public.password_reset_tokens (token);
CREATE INDEX IF NOT EXISTS idx_prt_user_id ON public.password_reset_tokens (user_id);

-- Limpiar tokens usados o expirados (ejecutar periódicamente si se desea)
-- DELETE FROM public.password_reset_tokens WHERE used = TRUE OR expires_at < NOW();
