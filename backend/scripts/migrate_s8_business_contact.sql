-- S8: datos de contacto del negocio (salen en el PDF de la OC). Aditiva.
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS address varchar;
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS phone varchar(30);
ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS email varchar;
