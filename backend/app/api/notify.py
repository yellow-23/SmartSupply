import os
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.notify_service import check_low_stock_and_notify, send_weekly_digest

router = APIRouter()

CRON_SECRET = os.environ["CRON_SECRET"]


def _verify_cron_secret(x_cron_secret: Annotated[str | None, Header()] = None) -> None:
    if x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Secret de cron invalido")


@router.post("/low-stock")
def trigger_low_stock_check(
    _: Annotated[None, Depends(_verify_cron_secret)],
    db: Session = Depends(get_db),
):
    """Llamado por un cron externo (GitHub Actions) para revisar stock bajo en todos los negocios."""
    return check_low_stock_and_notify(db)


@router.post("/weekly-digest")
def trigger_weekly_digest(
    _: Annotated[None, Depends(_verify_cron_secret)],
    db: Session = Depends(get_db),
):
    """Llamado por un cron externo (GitHub Actions) para mandar el resumen semanal."""
    return send_weekly_digest(db)
