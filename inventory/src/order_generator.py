from dataclasses import dataclass
from datetime import date


@dataclass
class PurchaseOrder:
    sku_id: str
    quantity: float
    trigger_stock: float
    policy: str
    created_at: date


class OrderGenerator:
    """Genera órdenes de compra automáticas para SKUs que cruzan el punto de reorden."""

    def generate(self, sku_id: str, current_stock: float, s: float, S: float, policy: str = "s_s") -> PurchaseOrder | None:
        # TODO: verificar si stock <= s y crear orden por (S - stock_actual) unidades
        # Aplicar restricciones de proveedor: MOQ, múltiplo de pack size
        pass
