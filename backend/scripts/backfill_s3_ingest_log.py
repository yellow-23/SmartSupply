"""
Crea un ingest_log sintetico ('carga historica') por cada (business_id, store_nbr)
existente en sales_history y asocia sus filas. Asigna owner_user_id a los negocios
que no lo tengan, usando el primer usuario con ese business_id.
Idempotente: salta filas que ya tienen ingest_id.
Uso: source venv/bin/activate && python3.11 backend/scripts/backfill_s3_ingest_log.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from dotenv import load_dotenv
load_dotenv(ROOT / "backend" / ".env")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
Session = sessionmaker(bind=engine)

OWNER_SQL = text("""
    UPDATE businesses b
    SET owner_user_id = (
        SELECT u.id FROM users u WHERE u.business_id = b.id ORDER BY u.id LIMIT 1
    )
    WHERE b.owner_user_id IS NULL
""")

BACKFILL_SQL = text("""
    WITH groups AS (
        SELECT business_id, store_nbr,
               MIN(date) AS d0, MAX(date) AS d1, COUNT(*) AS n,
               to_jsonb(array_agg(DISTINCT family)) AS fams
        FROM sales_history
        WHERE ingest_id IS NULL
        GROUP BY business_id, store_nbr
    ),
    ins AS (
        INSERT INTO ingest_log
            (business_id, store_nbr, user_id, filename, file_type, records_loaded,
             sales_unit, date_range_start, date_range_end, families, status)
        SELECT g.business_id, g.store_nbr, COALESCE(b.owner_user_id, 1),
               'carga historica', 'historic', g.n, 'units', g.d0, g.d1, g.fams, 'active'
        FROM groups g
        JOIN businesses b ON b.id = g.business_id
        RETURNING id, business_id, store_nbr
    )
    UPDATE sales_history s
    SET ingest_id = ins.id
    FROM ins
    WHERE s.business_id = ins.business_id
      AND s.store_nbr = ins.store_nbr
      AND s.ingest_id IS NULL
""")

with Session() as db:
    db.execute(OWNER_SQL)
    db.execute(BACKFILL_SQL)
    db.commit()
    remaining = db.execute(text("SELECT COUNT(*) FROM sales_history WHERE ingest_id IS NULL")).scalar()
    print(f"backfill completo. filas sin ingest_id restantes: {remaining}")
