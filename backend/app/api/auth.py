import os
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import Business, Store, User, UserBusiness

router = APIRouter()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_KEY"]

bearer_scheme = HTTPBearer()


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    business_id: int
    business_name: str = ""
    onboarding_completed: bool = True


class OnboardingRequest(BaseModel):
    business_name: str


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """Valida el token de Supabase Auth contra su API y resuelve/crea el usuario local.
    Primer login de un supabase_uid nunca visto: autoprovisiona negocio + tienda + usuario (mismo
    flujo que antes era /register). Cuenta vieja con el mismo email pero sin supabase_uid: se enlaza."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        resp = httpx.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {creds.credentials}"},
            timeout=10.0,
        )
    except httpx.HTTPError:
        raise exc
    if resp.status_code != 200:
        raise exc

    payload = resp.json()
    supabase_uid = payload.get("id")
    email = payload.get("email")
    if not supabase_uid or not email:
        raise exc

    user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
    if user:
        return user

    # Migracion: cuenta creada antes de Supabase Auth, mismo email, todavia sin enlazar.
    user = db.query(User).filter(User.email == email, User.supabase_uid.is_(None)).first()
    if user:
        user.supabase_uid = supabase_uid
        db.commit()
        db.refresh(user)
        return user

    # Primer login de este usuario en el sistema: autoprovisionar negocio + tienda + usuario.
    metadata = payload.get("user_metadata") or {}
    name = metadata.get("full_name") or metadata.get("name") or email.split("@")[0]
    given_business_name = (metadata.get("business_name") or "").strip()
    business_name = given_business_name or f"Negocio de {name}"

    business = Business(name=business_name, type="distributor", onboarding_completed=bool(given_business_name))
    db.add(business)
    db.flush()
    db.add(Store(business_id=business.id, store_nbr=1, name="Tienda Principal"))

    user = User(
        name=name,
        email=email,
        supabase_uid=supabase_uid,
        role="business_admin",
        business_id=business.id,
    )
    db.add(user)
    db.flush()
    business.owner_user_id = user.id
    db.add(UserBusiness(user_id=user.id, business_id=business.id, role="owner"))
    db.commit()
    db.refresh(user)
    return user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role != "business_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol de administrador")
    return current_user


def assert_business_access(db: Session, user: User, business_id: int) -> None:
    """Verifica que el usuario pertenezca al negocio antes de dejarlo leer/escribir sus datos."""
    has_access = db.query(UserBusiness).filter(
        UserBusiness.user_id == user.id,
        UserBusiness.business_id == business_id,
    ).first()
    if not has_access:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este negocio")


@router.get("/me", response_model=UserOut)
def me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Llamar despues de un login/signup con Supabase Auth para obtener el perfil local
    (crea negocio/tienda/usuario en el primer llamado, via get_current_user)."""
    biz = db.query(Business).filter(Business.id == current_user.business_id).first()
    return UserOut(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        business_id=current_user.business_id,
        business_name=biz.name if biz else "",
        onboarding_completed=biz.onboarding_completed if biz else True,
    )


@router.post("/onboarding", response_model=UserOut)
def complete_onboarding(
    body: OnboardingRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Completa el nombre del negocio para cuentas autoprovisionadas sin ese dato (ej: login con Google)."""
    name = body.business_name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="El nombre del negocio no puede estar vacío")

    biz = db.query(Business).filter(Business.id == current_user.business_id).first()
    if not biz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negocio no encontrado")

    biz.name = name
    biz.onboarding_completed = True
    db.commit()

    return UserOut(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        business_id=current_user.business_id,
        business_name=biz.name,
        onboarding_completed=True,
    )
