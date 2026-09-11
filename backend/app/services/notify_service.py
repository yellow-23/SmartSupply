"""
notify_service — envia correos de Stocky via Resend (stock bajo + resumen semanal).
Pensado para ser llamado desde un cron externo (GitHub Actions), no desde el usuario.
"""
import os
from datetime import timedelta

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

        items_html = ""
        for store_nbr, a in rows:
            if a.get("needs_cost_setup"):
                accion = "Configura el costo unitario en Productos para ver cuánto pedir"
            else:
                accion = f"Pedir {a['order_quantity']:.0f} unidades (punto de reorden: {a['reorder_point_s']:.0f})"
            items_html += f"""
                                    <tr>
                                        <td style="border-bottom: 1px solid #f5f5f4; padding-left: 0;">
                                            <strong style="color: #1c1917; font-size: 15px;">{a['family']}</strong><br>
                                            <span style="font-size: 13px; color: #78716c;">(tienda {store_nbr})</span>
                                        </td>
                                        <td align="center" style="border-bottom: 1px solid #f5f5f4; color: #cb3c31; font-weight: bold; font-size: 15px;">{a['current_stock']:.0f}</td>
                                        <td style="border-bottom: 1px solid #f5f5f4; font-size: 14px; color: #57534e; padding-right: 0; line-height: 1.4;">{accion}</td>
                                    </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alerta de Stock - SmartSupply</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8f6f3; color: #1c1917;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f8f6f3; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);">
                    <tr>
                        <td align="center" style="background-color: #ffffff; padding: 30px; text-align: center; border-bottom: 1px solid #f0ede9;">
                            <img src="https://i.postimg.cc/tJ7RZbQp/smartsupply-symbol.png" alt="SmartSupply" width="80" style="display: block; width: 80px; max-width: 100%; height: auto; margin: 0 auto;">
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 24px 0; font-size: 16px; line-height: 24px; color: #44403c;">Hola,</p>
                            <div style="background-color: #fff5f5; border-left: 4px solid #cb3c31; padding: 16px; margin-bottom: 30px; border-radius: 0 4px 4px 0;">
                                <p style="margin: 0; font-size: 16px; color: #991b1b; font-weight: 600;">
                                    Stocky detectó {len(rows)} producto(s) con stock por debajo del punto de reorden en "{business.name}":
                                </p>
                            </div>
                            <table width="100%" cellpadding="14" cellspacing="0" border="0" style="margin-bottom: 35px; border-collapse: collapse;">
                                <thead>
                                    <tr>
                                        <th align="left" style="border-bottom: 2px solid #e7e5e4; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #78716c; padding-left: 0;">Producto</th>
                                        <th align="center" style="border-bottom: 2px solid #e7e5e4; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #78716c;">Stock</th>
                                        <th align="left" style="border-bottom: 2px solid #e7e5e4; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #78716c; padding-right: 0;">Acción Requerida</th>
                                    </tr>
                                </thead>
                                <tbody>{items_html}
                                </tbody>
                            </table>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td align="center">
                                        <a href="https://app.smart-supply.cl/login" style="display: inline-block; padding: 14px 28px; background-color: #231f20; color: #ffffff; text-decoration: none; font-size: 15px; font-weight: 500; border-radius: 8px;">Entrar a SmartSupply</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="background-color: #faf9f8; padding: 24px; text-align: center; border-top: 1px solid #e7e5e4;">
                            <p style="margin: 0; font-size: 12px; color: #78716c; line-height: 18px;">
                                Estás recibiendo este correo porque tienes alertas de inventario activas en <strong>SmartSupply</strong>.<br>
                                Por favor, no respondas a este mensaje.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
        if send_email(owner_email, f"⚠ Stock bajo en {business.name}", html):
            sent += 1
        else:
            skipped += 1

    return {"sent": sent, "skipped": skipped}


def send_weekly_digest(db: Session) -> dict:
    """Resumen semanal por negocio: ventas de los ultimos 7 dias, MAPE del AMS,
    ordenes pendientes y alertas de stock activas."""
    sent, skipped = 0, 0
    for business in db.query(Business).all():
        owner_email = _owner_email(db, business)
        if not owner_email:
            skipped += 1
            continue

        # Ventana movil sobre la ultima fecha con datos del negocio (no sobre "hoy" real):
        # asi el resumen tiene sentido aunque la ultima carga sea de hace tiempo.
        latest_date = (
            db.query(func.max(SalesHistory.date))
            .filter(SalesHistory.business_id == business.id)
            .scalar()
        )
        if latest_date is None:
            continue  # negocio sin ninguna venta cargada: no le mandamos un digest vacio
        today = latest_date
        week_ago = today - timedelta(days=6)

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
            continue

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