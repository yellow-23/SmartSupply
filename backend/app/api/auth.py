import os
import secrets
import threading
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orm import Business, PasswordResetToken, Store, User

router = APIRouter()

_SECRET = os.environ.get("JWT_SECRET", "changeme-set-in-env")
_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
_EXPIRE_HOURS = int(os.environ.get("JWT_EXPIRE_HOURS", "8"))
_DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_MAX_ATTEMPTS = 5
_WINDOW_MINUTES = 15
_rate_lock = threading.Lock()
_failed_attempts: dict[str, dict] = defaultdict(lambda: {"count": 0, "window_start": datetime.now(timezone.utc)})


def _check_rate_limit(ip: str) -> None:
    with _rate_lock:
        entry = _failed_attempts[ip]
        now = datetime.now(timezone.utc)
        if (now - entry["window_start"]).total_seconds() > _WINDOW_MINUTES * 60:
            entry["count"] = 0
            entry["window_start"] = now
        if entry["count"] >= _MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiados intentos fallidos. Intenta de nuevo en {_WINDOW_MINUTES} minutos.",
            )


def _record_failure(ip: str) -> None:
    with _rate_lock:
        entry = _failed_attempts[ip]
        now = datetime.now(timezone.utc)
        if (now - entry["window_start"]).total_seconds() > _WINDOW_MINUTES * 60:
            entry["count"] = 0
            entry["window_start"] = now
        entry["count"] += 1


def _clear_rate_limit(ip: str) -> None:
    with _rate_lock:
        _failed_attempts[ip] = {"count": 0, "window_start": datetime.now(timezone.utc)}



class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    business_name: str = ""  # nombre del negocio; si vacío usa "Negocio de {name}"
    role: str = "analyst"


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    business_id: int
    business_name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def _verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(user.id), "role": user.role, "business_id": user.business_id, "exp": exp},
        _SECRET,
        algorithm=_ALGORITHM,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip)

    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user or not _verify_password(body.password, user.hashed_password):
        _record_failure(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    _clear_rate_limit(ip)
    biz = db.query(Business).filter(Business.id == user.business_id).first()
    return TokenResponse(
        access_token=_create_token(user),
        user=UserOut(id=user.id, name=user.name, email=user.email, role=user.role, business_id=user.business_id, business_name=biz.name if biz else ""),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if body.role not in ("admin", "analyst"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Rol debe ser 'admin' o 'analyst'")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El correo ya está registrado")

    biz_name = body.business_name.strip() or f"Negocio de {body.name}"
    business = Business(name=biz_name, type="distributor")
    db.add(business)
    db.flush()

    store = Store(business_id=business.id, store_nbr=1, name="Tienda Principal")
    db.add(store)

    hashed = _bcrypt.hashpw(body.password.encode(), _bcrypt.gensalt()).decode()
    user = User(
        name=body.name,
        email=body.email,
        hashed_password=hashed,
        role="admin",
        business_id=business.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(
        access_token=_create_token(user),
        user=UserOut(id=user.id, name=user.name, email=user.email, role=user.role, business_id=user.business_id, business_name=biz_name),
    )


@router.post("/forgot-password", status_code=200)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Genera un token de recuperación con TTL 30 min.
    Responde siempre 200 para no revelar si el email existe.
    En DEBUG=true devuelve el token para facilitar pruebas sin SMTP.
    TODO: enviar email real via SMTP/Resend cuando se configure.
    """
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user:
        response = {"message": "Si el correo está registrado, recibirás un enlace de recuperación."}
        if _DEBUG:
            response["debug_token"] = None
        return response

    token_value = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    reset_token = PasswordResetToken(user_id=user.id, token=token_value, expires_at=expires_at)
    db.add(reset_token)
    db.commit()


    response: dict = {"message": "Si el correo está registrado, recibirás un enlace de recuperación."}
    if _DEBUG:
        response["debug_token"] = token_value
    return response


@router.post("/reset-password", status_code=200)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Valida el token, actualiza la contraseña y marca el token como usado."""
    if len(body.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La contraseña debe tener al menos 8 caracteres")

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == body.token,
        PasswordResetToken.used == False,
    ).first()

    if not reset_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido o ya utilizado")

    if datetime.now(timezone.utc) > reset_token.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El enlace de recuperación ha expirado")

    user = db.query(User).filter(User.id == reset_token.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario no encontrado")

    user.hashed_password = _bcrypt.hashpw(body.new_password.encode(), _bcrypt.gensalt()).decode()
    reset_token.used = True
    db.commit()

    return {"message": "Contraseña actualizada exitosamente"}



def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _SECRET, algorithms=[_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise exc
    except JWTError:
        raise exc
    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not user:
        raise exc
    return user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol de administrador")
    return current_user

