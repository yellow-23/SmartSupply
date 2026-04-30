# ETL — SmartSupply

Pipeline para cargar el dataset de Kaggle a la base de datos.

## Pasos

```bash
# 1. Extraer el dataset
python scripts/01_download_kaggle.py

# 2. Limpiar y normalizar
python scripts/02_clean.py

# 3. Cargar a PostgreSQL / Supabase
python scripts/03_load_supabase.py
```

Requiere `backend/.env` con `DATABASE_URL` configurado antes de correr el paso 3.
