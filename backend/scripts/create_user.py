"""
Crea un usuario en la tabla users.
Uso: cd backend && python3.11 scripts/create_user.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import bcrypt
from app.database import SessionLocal, engine
from app.models.orm import User, Base

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    if db.query(User).filter(User.email == "cristobal@distribuidora.cl").first():
        print("El usuario ya existe.")
        sys.exit(0)

    hashed = bcrypt.hashpw(b"demo1234", bcrypt.gensalt()).decode()
    db.add(User(
        name="Cristóbal Flores",
        email="cristobal@distribuidora.cl",
        hashed_password=hashed,
        role="admin",
        business_id=1,
    ))
    db.commit()
    print("Usuario creado: cristobal@distribuidora.cl / demo1234")
finally:
    db.close()
