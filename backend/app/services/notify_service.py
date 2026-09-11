"""
notify_service — envia correos de Stocky via Resend (stock bajo + resumen semanal).
Pensado para ser llamado desde un cron externo (GitHub Actions), no desde el usuario.
"""
import os
from datetime import date, timedelta
from html import escape

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.orm import Business, PurchaseOrder, SalesHistory, Store, User
from app.services.forecast_service import get_business_wapes
from app.services.inventory_service import InventoryService

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "Stocky <stocky@smart-supply.cl>")

APP_URL = "https://app.smart-supply.cl"
# PNG del simbolo de la app (frontend/public/email/logo.png); Gmail no muestra SVG
LOGO_URL = f"{APP_URL}/email/logo.png"
FONT = "'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

_inventory = InventoryService()


def send_email(to: str, subject: str, html: str) -> bool:
    """Envia un correo via la API HTTP de Resend. Devuelve False (sin lanzar) si falla,
    para que un negocio con error de envio no corte el resto del batch."""
    if not RESEND_API_KEY:
        print("[notify] RESEND_API_KEY no configurada, no se envia correo")
        return False
    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={"from": RESEND_FROM_EMAIL, "to": [to], "subject": subject, "html": html},
            timeout=15.0,
        )
    except httpx.HTTPError as e:
        print(f"[notify] error de red enviando a {to}: {e}")
        return False
    if resp.status_code >= 300:
        print(f"[notify] Resend rechazo envio a {to}: {resp.status_code} {resp.text}")
        return False
    return True


def _num(n: float) -> str:
    """Formato chileno: separador de miles con punto."""
    return f"{n:,.0f}".replace(",", ".")


def _layout(business_name: str, preheader: str, body: str, cta_label: str, cta_path: str) -> str:
    """Marco comun de los correos: barra navy con el logo como el sidebar de la app,
    tarjeta blanca y boton naranjo."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SmartSupply</title>
</head>
<body style="margin:0;padding:0;background:#F5F7FA;font-family:{FONT};color:#111827;">
<div style="display:none;max-height:0;overflow:hidden;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F5F7FA;">
<tr><td align="center" style="padding:32px 8px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;">
    <tr><td style="background:#1A1A2E;padding:18px 24px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
        <td style="vertical-align:middle;">
          <img src="{LOGO_URL}" width="28" height="28" alt="" style="display:inline-block;vertical-align:middle;border:0;">
          <span style="vertical-align:middle;margin-left:10px;font-size:17px;font-weight:700;color:#FFFFFF;letter-spacing:-0.2px;">SmartSupply</span>
        </td>
        <td align="right" style="vertical-align:middle;font-size:12px;font-weight:600;color:#FB923C;">{business_name}</td>
      </tr></table>
    </td></tr>
    <tr><td style="padding:32px 24px;">
      {body}
      <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-top:28px;"><tr>
        <td style="background:#EA580C;border-radius:8px;">
          <a href="{APP_URL}{cta_path}" style="display:inline-block;padding:12px 22px;font-size:14px;font-weight:600;color:#FFFFFF;text-decoration:none;">{cta_label}</a>
        </td>
      </tr></table>
    </td></tr>
    <tr><td style="padding:18px 24px;background:#F9FAFB;border-top:1px solid #F3F4F6;font-size:12px;line-height:18px;color:#9CA3AF;">
      Correo automático de Stocky, tu asistente de inventario en SmartSupply. No respondas a este mensaje.
    </td></tr>
  </table>
</td></tr>
</table>
</body>
</html>"""


def _heading(eyebrow: str, eyebrow_color: str, title: str, subtitle: str) -> str:
    return (
        f'<p style="margin:0 0 6px;font-size:12px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:{eyebrow_color};">{eyebrow}</p>'
        f'<h1 style="margin:0 0 8px;font-size:22px;line-height:30px;font-weight:700;color:#111827;">{title}</h1>'
        f'<p style="margin:0 0 24px;font-size:14px;line-height:22px;color:#6B7280;">{subtitle}</p>'
    )


def low_stock_html(business_name: str, rows: list[tuple[int, dict]]) -> str:
    """rows: [(store_nbr, alerta de get_critical_skus), ...]"""
    biz = escape(business_name)
    multi_store = len({s for s, _ in rows}) > 1
    th = "padding:10px 8px;font-size:11px;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;color:#6B7280;border-bottom:1px solid #E5E7EB;"
    td = "padding:12px 8px;font-size:14px;border-bottom:1px solid #F3F4F6;"

    items = ""
    for store_nbr, a in rows:
        tienda = f'<br><span style="font-size:12px;color:#9CA3AF;">Tienda {store_nbr}</span>' if multi_store else ""
        if a.get("needs_cost_setup"):
            sugerido = '<span style="display:inline-block;padding:2px 8px;white-space:nowrap;border-radius:999px;background:#FFFBEB;color:#B45309;font-size:12px;font-weight:600;">Falta costo</span>'
        else:
            sugerido = f'<strong style="color:#111827;white-space:nowrap;">{_num(a["order_quantity"])} uds</strong>'
        items += (
            f'<tr><td style="{td}color:#111827;font-weight:600;">{escape(a["family"])}{tienda}</td>'
            f'<td align="right" style="{td}color:#C62828;font-weight:700;">{_num(a["current_stock"])}</td>'
            f'<td align="right" style="{td}color:#4B5563;">{_num(a["reorder_point_s"])}</td>'
            f'<td align="right" style="{td}">{sugerido}</td></tr>'
        )

    n = len(rows)
    title = f"{n} producto{'s' if n != 1 else ''} bajo el punto de reorden"
    nota = ""
    if any(a.get("needs_cost_setup") for _, a in rows):
        nota = (
            '<p style="margin:16px 0 0;font-size:13px;line-height:20px;color:#6B7280;">'
            '<strong style="color:#B45309;">Falta costo:</strong> configura el costo unitario en Productos '
            'para que Stocky calcule cuánto pedir.</p>'
        )
    body = (
        _heading("Alerta de stock", "#C62828", title,
                 f"Stocky revisó el inventario de <strong style=\"color:#111827;\">{biz}</strong> y estos productos necesitan reposición.")
        + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid #E5E7EB;border-radius:10px;border-collapse:separate;overflow:hidden;">'
        + f'<tr style="background:#F9FAFB;"><th align="left" style="{th}">Producto</th><th align="right" style="{th}">Stock</th>'
        + f'<th align="right" style="{th}">Reorden</th><th align="right" style="{th}">Sugerido</th></tr>'
        + items
        + "</table>"
        + nota
    )
    return _layout(biz, title, body, "Ver inventario", "/inventory")


def weekly_digest_html(
    business_name: str, start: date, end: date, total_sales: float, sales_unit: str,
    mape: float | None, pending_orders: int, critical_count: int,
) -> str:
    biz = escape(business_name)
    ventas = f"${_num(total_sales)}" if sales_unit == "CLP" else f"{_num(total_sales)} uds"
    rango = f"Del {start.day} de {MESES[start.month - 1]} al {end.day} de {MESES[end.month - 1]} de {end.year}"

    def tile(label: str, value: str, hint: str, color: str = "#111827", left: bool = True) -> str:
        pad = "0 6px 12px 0" if left else "0 0 12px 6px"
        return (
            f'<td width="50%" style="padding:{pad};vertical-align:top;">'
            '<div style="background:#F9FAFB;border:1px solid #F3F4F6;border-radius:10px;padding:16px;">'
            f'<p style="margin:0 0 6px;font-size:12px;font-weight:600;color:#6B7280;">{label}</p>'
            f'<p style="margin:0 0 4px;font-size:24px;line-height:30px;font-weight:700;color:{color};">{value}</p>'
            f'<p style="margin:0;font-size:12px;color:#9CA3AF;">{hint}</p>'
            "</div></td>"
        )

    body = (
        _heading("Resumen semanal", "#EA580C", f"Tu semana en {biz}", rango)
        + '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" >'
        + "<tr>"
        + tile("Ventas de la semana", ventas, "Últimos 7 días con datos")
        + tile("MAPE del pronóstico", f"{str(mape).replace('.', ',')}%" if mape is not None else "Sin datos",
               "Error promedio, menor es mejor" if mape is not None else "Corre un pronóstico para verlo", left=False)
        + "</tr><tr>"
        + tile("Órdenes pendientes", str(pending_orders), "Por confirmar o recibir")
        + tile("Productos en alerta", str(critical_count),
               "Bajo el punto de reorden" if critical_count else "Todo en orden",
               "#C62828" if critical_count else "#2E7D32", left=False)
        + "</tr></table>"
    )
    return _layout(biz, f"{rango}: ventas {ventas}, {critical_count} productos en alerta", body, "Ver panel", "/dashboard")


def _owner_email(db: Session, business: Business) -> str | None:
    if not business.owner_user_id:
        return None
    owner = db.query(User).filter(User.id == business.owner_user_id).first()
    return owner.email if owner else None


def _businesses(db: Session, business_id: int | None):
    q = db.query(Business)
    return q.filter(Business.id == business_id).all() if business_id else q.all()


def check_low_stock_and_notify(db: Session, business_id: int | None = None) -> dict:
    """Para cada negocio, revisa SKUs criticos (stock <= punto de reorden) en todas sus
    tiendas y le manda un correo al dueño si hay al menos uno."""
    sent, skipped = 0, 0
    for business in _businesses(db, business_id):
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

        if send_email(owner_email, f"Stock bajo en {business.name}", low_stock_html(business.name, rows)):
            sent += 1
        else:
            skipped += 1

    return {"sent": sent, "skipped": skipped}


def send_weekly_digest(db: Session, business_id: int | None = None) -> dict:
    """Resumen semanal por negocio: ventas de los ultimos 7 dias, MAPE del AMS,
    ordenes pendientes y alertas de stock activas."""
    sent, skipped = 0, 0
    for business in _businesses(db, business_id):
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

        # ponytail: toma la unidad de una fila cualquiera; un negocio con cargas CLP y uds mezcladas mostraria solo una
        sales_unit = (
            db.query(SalesHistory.sales_unit).filter(SalesHistory.business_id == business.id).limit(1).scalar()
            or "units"
        )
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

        html = weekly_digest_html(
            business.name, week_ago, today, total_sales, sales_unit, mape, pending_orders, critical_count,
        )
        if send_email(owner_email, f"Resumen semanal de {business.name}", html):
            sent += 1
        else:
            skipped += 1

    return {"sent": sent, "skipped": skipped}
