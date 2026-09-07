"""
notify_service — envia correos de Stocky via Resend (stock bajo + resumen semanal).
Pensado para ser llamado desde un cron externo (GitHub Actions), no desde el usuario.
"""
import os
from datetime import date, timedelta

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.orm import Business, PurchaseOrder, SalesHistory, Store, User
from app.services.forecast_service import get_business_wapes
from app.services.inventory_service import InventoryService

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "Stocky <stocky@smart-supply.cl>")

_inventory = InventoryService()


def send_email(to: str, subject: str, html: str) -> bool:
    """Envia un correo via la API HTTP de Resend. Devuelve False (sin lanzar) si falla,
    para que un negocio con error de envio no corte el resto del batch."""
    if not RESEND_API_KEY:
        return False
    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": RESEND_FROM_EMAIL, "to": [to], "subject": subject, "html": html},
            timeout=15.0,
        )
        return resp.status_code < 300
    except httpx.HTTPError:
        return False


def _owner_email(db: Session, business: Business) -> str | None:
    if not business.owner_user_id:
        return None
    owner = db.query(User).filter(User.id == business.owner_user_id).first()
    return owner.email if owner else None


def check_low_stock_and_notify(db: Session) -> dict:
    """Para cada negocio, revisa SKUs criticos (stock <= punto de reorden) en todas sus
    tiendas y le manda un correo al dueño si hay al menos uno."""
    sent, skipped = 0, 0
    for business in db.query(Business).all():
        owner_email = _owner_email(db, business)
        if not owner_email:
            skipped += 1
            continue

        rows = []
        for store in db.query(Store).filter(Store.business_id == business.id).all():
            for alert in _inventory.get_critical_skus(db, business.id, store.store_nbr):
                rows.append((store.store_nbr, alert))

        if not rows:
            continue

        items_html = "".join(
            f"<li><b>{a['family']}</b> (tienda {store_nbr}): stock {a['current_stock']:.0f}"
            + (
                f", punto de reorden {a['reorder_point_s']:.0f}, sugerido pedir {a['order_quantity']:.0f}</li>"
                if not a.get("needs_cost_setup")
                else " — configura el costo unitario en Productos para ver cuánto pedir</li>"
            )
            for store_nbr, a in rows
        )
        html = (
            f"<p>Hola,</p>"
            f"<p>Stocky detectó <b>{len(rows)} producto(s)</b> con stock por debajo del punto de reorden en "
            f"<b>{business.name}</b>:</p>"
            f"<ul>{items_html}</ul>"
            f"<p>Entra a SmartSupply para generar las órdenes de compra.</p>"
        )
        if send_email(owner_email, f"⚠ Stock bajo en {business.name}", html):
            sent += 1
        else:
            skipped += 1

    return {"sent": sent, "skipped": skipped}


def send_weekly_digest(db: Session) -> dict:
    """Resumen semanal por negocio: ventas de los ultimos 7 dias, MAPE del AMS,
    ordenes pendientes y alertas de stock activas."""
    sent, skipped = 0, 0
    today = date.today()
    week_ago = today - timedelta(days=7)

    for business in db.query(Business).all():
        owner_email = _owner_email(db, business)
        if not owner_email:
            skipped += 1
            continue

        total_sales = (
            db.query(func.sum(SalesHistory.sales))
            .filter(
                SalesHistory.business_id == business.id,
                SalesHistory.date >= week_ago,
                SalesHistory.date <= today,
            )
            .scalar()
        )
        if total_sales is None:
            continue  # negocio sin datos esta semana: no le mandamos un digest vacio

        pending_orders = (
            db.query(func.count(PurchaseOrder.id))
            .filter(PurchaseOrder.business_id == business.id, PurchaseOrder.status == "pending")
            .scalar()
            or 0
        )
        wapes = get_business_wapes(business.id)
        mape = round(sum(wapes) / len(wapes), 1) if wapes else None

        critical_count = 0
        for store in db.query(Store).filter(Store.business_id == business.id).all():
            critical_count += len(_inventory.get_critical_skus(db, business.id, store.store_nbr))

        html = (
            f"<p>Hola, este es tu resumen semanal de <b>{business.name}</b> "
            f"({week_ago.isoformat()} a {today.isoformat()}):</p>"
            f"<ul>"
            f"<li>Ventas totales: {total_sales:,.0f}</li>"
            f"<li>Precisión del modelo (MAPE): {f'{mape}%' if mape is not None else 'sin datos aún'}</li>"
            f"<li>Órdenes de compra pendientes: {pending_orders}</li>"
            f"<li>SKUs en alerta de stock: {critical_count}</li>"
            f"</ul>"
            f"<p>Entra a SmartSupply para ver el detalle.</p>"
        )
        if send_email(owner_email, f"Resumen semanal — {business.name}", html):
            sent += 1
        else:
            skipped += 1

    return {"sent": sent, "skipped": skipped}
