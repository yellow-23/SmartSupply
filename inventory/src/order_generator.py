import math
from dataclasses import dataclass, field
from datetime import date


@dataclass
class PurchaseOrder:
    sku_id: str
    quantity: float
    trigger_stock: float
    policy: str
    created_at: date
    reorder_point_s: float = 0.0
    order_up_to_S: float = 0.0
    store_nbr: int = 1
    family: str = ""


class OrderGenerator:
    """Genera órdenes de compra automáticas para SKUs que cruzan el punto de reorden."""

    def __init__(self, moq: float = 0.0, pack_size: float = 1.0):
        self.moq = moq
        self.pack_size = pack_size

    def generate(self, sku_id: str, current_stock: float, s: float, S: float, policy: str = "s_s") -> PurchaseOrder | None:
        if current_stock > s:
            return None
        raw_quantity = max(0.0, S - current_stock)
        quantity = max(raw_quantity, self.moq)
        quantity = math.ceil(quantity / self.pack_size) * self.pack_size
        return PurchaseOrder(
            sku_id=sku_id,
            quantity=quantity,
            trigger_stock=current_stock,
            policy=policy,
            created_at=date.today(),
            reorder_point_s=s,
            order_up_to_S=S,
            store_nbr=1,
            family=sku_id,
        )

    def generate_bulk(self, skus: list[dict]) -> list[PurchaseOrder]:
        orders = []
        for sku in skus:
            order = self.generate(
                sku_id=sku["sku_id"],
                current_stock=sku["current_stock"],
                s=sku["s"],
                S=sku["S"],
            )
            if order is not None:
                orders.append(order)
        return orders
