-- S9: proyeccion de venta total por ubicacion persistida (Dashboard). Aditiva.
CREATE TABLE IF NOT EXISTS public.store_forecasts (
    id serial PRIMARY KEY,
    business_id integer NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    store_nbr integer NOT NULL,
    horizon_days integer NOT NULL,
    fingerprint varchar NOT NULL,
    computed_on date NOT NULL,
    payload json NOT NULL,
    created_at timestamptz DEFAULT now(),
    UNIQUE (business_id, store_nbr, horizon_days)
);
CREATE INDEX IF NOT EXISTS ix_store_forecasts_business_id ON public.store_forecasts(business_id);
-- Sin politicas: el anon key no la lee (el backend usa postgres/bypassrls), igual que el resto.
ALTER TABLE public.store_forecasts ENABLE ROW LEVEL SECURITY;
