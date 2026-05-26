"""
StockyService — Asistente IA con herramientas de BD
Loop agéntico: Claude decide qué tool llamar, el backend ejecuta, Claude procesa y responde.
"""
import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.models.orm import Product, StockLevel, PurchaseOrder

load_dotenv(Path(__file__).parents[3] / "backend" / ".env")

_SYSTEM = """Eres Stocky, el asistente de inventario de SmartSupply para distribuidoras chilenas.

Tienes herramientas para consultar y actualizar la base de datos en tiempo real.
Cuando el usuario pregunta por datos o problemas, úsalas antes de responder.
Cuando el usuario confirme una acción, ejecútala directamente.

Reglas:
- Responde siempre en español, sé directo y conciso
- Para costos usa formato chileno: $1.500 no 1500
- Usa listas cuando presentes múltiples registros
- Si vas a modificar datos, confirma brevemente qué cambiaste y qué valor quedó"""

_TOOLS = [
    {
        "name": "list_products",
        "description": "Lista productos del negocio con sus parámetros. Útil para detectar campos faltantes (unit_cost, holding_rate, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "store_nbr": {"type": "integer", "description": "Filtrar por tienda (opcional)"},
                "missing_only": {"type": "boolean", "description": "Si true, solo devuelve productos con algún campo nulo"}
            }
        }
    },
    {
        "name": "list_stock_levels",
        "description": "Lista niveles de stock actuales del negocio.",
        "input_schema": {
            "type": "object",
            "properties": {
                "store_nbr": {"type": "integer", "description": "Filtrar por tienda (opcional)"}
            }
        }
    },
    {
        "name": "list_orders",
        "description": "Lista órdenes de compra del negocio.",
        "input_schema": {
            "type": "object",
            "properties": {
                "store_nbr": {"type": "integer", "description": "Filtrar por tienda (opcional)"},
                "status": {"type": "string", "description": "Estado: pending, confirmed, in_transit, received, cancelled"}
            }
        }
    },
    {
        "name": "update_product",
        "description": "Actualiza o crea parámetros de un producto. Solo modifica los campos que se pasen explícitamente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "family": {"type": "string", "description": "Nombre de la familia (ej: BEBIDAS)"},
                "store_nbr": {"type": "integer", "description": "Número de tienda"},
                "unit_cost": {"type": "number", "description": "Costo unitario en CLP"},
                "order_cost": {"type": "number", "description": "Costo fijo por pedido en CLP"},
                "holding_rate": {"type": "number", "description": "Tasa de almacenamiento anual (ej: 0.25 = 25%)"},
                "lead_time_days": {"type": "integer", "description": "Días de lead time del proveedor"},
                "moq": {"type": "number", "description": "Cantidad mínima de orden"}
            },
            "required": ["family", "store_nbr"]
        }
    },
    {
        "name": "update_stock_level",
        "description": "Actualiza el nivel de stock de una familia en una tienda.",
        "input_schema": {
            "type": "object",
            "properties": {
                "family": {"type": "string", "description": "Nombre de la familia"},
                "store_nbr": {"type": "integer", "description": "Número de tienda"},
                "quantity": {"type": "number", "description": "Cantidad actual en inventario"}
            },
            "required": ["family", "store_nbr", "quantity"]
        }
    }
]


def _list_products(db: Session, business_id: int, inp: dict) -> str:
    store_nbr = inp.get("store_nbr")
    missing_only = inp.get("missing_only", False)

    q = db.query(Product).filter(Product.business_id == business_id)
    if store_nbr:
        q = q.filter(Product.store_nbr == store_nbr)
    products = q.all()

    if not products:
        return "No hay productos configurados para este negocio."

    rows = []
    for p in products:
        missing = [
            f for f, v in [
                ("unit_cost", p.unit_cost),
                ("order_cost", p.order_cost),
                ("holding_rate", p.holding_rate),
                ("lead_time_days", p.lead_time_days),
            ] if v is None
        ]
        if missing_only and not missing:
            continue
        rows.append({
            "family": p.family,
            "store_nbr": p.store_nbr,
            "unit_cost": float(p.unit_cost) if p.unit_cost is not None else None,
            "order_cost": float(p.order_cost) if p.order_cost is not None else None,
            "holding_rate": float(p.holding_rate) if p.holding_rate is not None else None,
            "lead_time_days": p.lead_time_days,
            "moq": float(p.moq) if p.moq is not None else None,
            "missing_fields": missing,
        })

    if not rows:
        return "Todos los productos tienen sus parámetros completos."
    return json.dumps(rows, ensure_ascii=False)


def _list_stock(db: Session, business_id: int, inp: dict) -> str:
    store_nbr = inp.get("store_nbr")
    q = db.query(StockLevel).filter(StockLevel.business_id == business_id)
    if store_nbr:
        q = q.filter(StockLevel.store_nbr == store_nbr)
    stocks = q.all()
    if not stocks:
        return "No hay niveles de stock registrados."
    rows = [{"family": s.family, "store_nbr": s.store_nbr, "quantity": float(s.quantity)} for s in stocks]
    return json.dumps(rows, ensure_ascii=False)


def _list_orders(db: Session, business_id: int, inp: dict) -> str:
    store_nbr = inp.get("store_nbr")
    status = inp.get("status")
    q = db.query(PurchaseOrder).filter(PurchaseOrder.business_id == business_id)
    if store_nbr:
        q = q.filter(PurchaseOrder.store_nbr == store_nbr)
    if status:
        q = q.filter(PurchaseOrder.status == status)
    orders = q.order_by(PurchaseOrder.created_at.desc()).limit(50).all()
    if not orders:
        return "No hay órdenes de compra."
    rows = [{
        "id": o.id,
        "family": o.family,
        "store_nbr": o.store_nbr,
        "quantity": float(o.quantity),
        "status": o.status,
        "created_at": str(o.created_at.date()) if o.created_at else None,
        "expected_delivery": str(o.expected_delivery) if o.expected_delivery else None,
    } for o in orders]
    return json.dumps(rows, ensure_ascii=False)


def _update_product(db: Session, business_id: int, inp: dict) -> str:
    family = inp["family"].upper()
    store_nbr = inp["store_nbr"]

    product = db.query(Product).filter(
        Product.business_id == business_id,
        Product.store_nbr == store_nbr,
        Product.family == family,
    ).first()

    created = False
    if product is None:
        product = Product(business_id=business_id, store_nbr=store_nbr, family=family)
        db.add(product)
        created = True

    updated = []
    for field in ["unit_cost", "order_cost", "holding_rate", "lead_time_days", "moq"]:
        if field in inp and inp[field] is not None:
            setattr(product, field, inp[field])
            updated.append(f"{field}={inp[field]}")

    db.commit()
    verb = "Creado" if created else "Actualizado"
    return f"{verb}: {family} tienda {store_nbr}. {', '.join(updated) if updated else 'Sin cambios.'}"


def _update_stock(db: Session, business_id: int, inp: dict) -> str:
    family = inp["family"].upper()
    store_nbr = inp["store_nbr"]
    quantity = inp["quantity"]

    stock = db.query(StockLevel).filter(
        StockLevel.business_id == business_id,
        StockLevel.store_nbr == store_nbr,
        StockLevel.family == family,
    ).first()

    if stock is None:
        stock = StockLevel(business_id=business_id, store_nbr=store_nbr, family=family, quantity=quantity)
        db.add(stock)
        verb = "Creado"
    else:
        stock.quantity = quantity
        verb = "Actualizado"

    db.commit()
    return f"{verb}: stock de {family} tienda {store_nbr} = {quantity}."


def _run_tool(db: Session, business_id: int, name: str, inp: dict) -> str:
    try:
        dispatch = {
            "list_products": _list_products,
            "list_stock_levels": _list_stock,
            "list_orders": _list_orders,
            "update_product": _update_product,
            "update_stock_level": _update_stock,
        }
        fn = dispatch.get(name)
        if fn is None:
            return f"Herramienta desconocida: {name}"
        return fn(db, business_id, inp)
    except Exception as e:
        return f"Error en {name}: {str(e)}"


def chat(db: Session, business_id: int, messages: list[dict], max_iterations: int = 6) -> str:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    history = [{"role": m["role"], "content": m["content"]} for m in messages]

    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=_SYSTEM,
            tools=_TOOLS,
            messages=history,
        )

        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            texts = [b for b in response.content if b.type == "text"]
            return texts[0].text if texts else ""

        # Append assistant turn (may include text preamble + tool_use blocks)
        history.append({"role": "assistant", "content": response.content})

        # Execute each tool and collect results
        results = []
        for tu in tool_uses:
            result = _run_tool(db, business_id, tu.name, tu.input)
            results.append({"type": "tool_result", "tool_use_id": tu.id, "content": result})

        history.append({"role": "user", "content": results})

    return "No pude completar la tarea. Intenta con una pregunta más específica."
