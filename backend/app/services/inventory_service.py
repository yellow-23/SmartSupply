"""
InventoryService — SmartSupply
Capa de servicio que conecta los endpoints de la API con los módulos de inventario.
"""

import math
from datetime import datetime, date, timedelta
from typing import Literal

from app.models.schemas import InventoryStatus, InventoryMetrics


class InventoryService:
    """
    Servicio de gestión de inventario.

    En producción conecta con inventory/src/ (EOQ, política (s,S), simulador).
    Por ahora retorna datos de ejemplo para que la API sea funcional.
    """

    def get_status(self, sku_id: str, store_nbr: int) -> InventoryStatus:
        """
        Retorna el estado actual del inventario para un SKU.

        Flujo real (a implementar):
        1. Consultar stock actual desde la BD
        2. Obtener predicción de demanda del ForecastService para el lead time
        3. Llamar a inventory/src/s_s_policy.py para calcular s y S actualizados
        4. Llamar a inventory/src/eoq.py para calcular EOQ
        5. Determinar si el stock actual < s (needs_reorder)
        """
        # TODO: Reemplazar con datos reales de BD + módulo inventory/
        mock_stock = 45.0
        mock_s = 30.0      # Punto de reorden (s)
        mock_S = 120.0     # Nivel de reposición (S)
        mock_eoq = 90.0

        return InventoryStatus(
            sku_id=sku_id,
            store_nbr=store_nbr,
            current_stock=mock_stock,
            reorder_point_s=mock_s,
            order_up_to_S=mock_S,
            eoq=mock_eoq,
            policy="s_s",
            needs_reorder=mock_stock <= mock_s,
            days_until_stockout=self._estimate_days_until_stockout(mock_stock, daily_demand=5.0),
            updated_at=datetime.now(),
        )

    def get_metrics(self, sku_id: str, store_nbr: int, period_days: int) -> InventoryMetrics:
        """
        Retorna métricas de desempeño de la política de inventario.

        TODO: Conectar con inventory/src/simulator.py para obtener métricas reales
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)

        return InventoryMetrics(
            sku_id=sku_id,
            store_nbr=store_nbr,
            period_start=start_date,
            period_end=end_date,
            capital_inmovilizado=52_500.0,    # TODO: calcular real desde simulador
            stockout_rate=3.2,
            inventory_turnover=12.4,
            service_level=96.8,
            total_inventory_cost=18_200.0,
        )

    def get_critical_skus(self, store_nbr: int) -> list[dict]:
        """
        Retorna los SKUs cuyo stock actual está por debajo del punto de reorden.
        Usados para generar órdenes automáticas.

        TODO: Consultar BD y cruzar con política (s,S) calculada dinámicamente
        """
        # Placeholder — en producción consulta la BD
        return [
            {
                "sku_id": "GROCERY-001",
                "current_stock": 12.0,
                "reorder_point_s": 30.0,
                "order_quantity": 90.0,
                "policy": "s_s",
            }
        ]

    def _estimate_days_until_stockout(self, stock: float, daily_demand: float) -> float:
        """Estimación simple de días hasta quiebre de stock."""
        if daily_demand <= 0:
            return float("inf")
        return round(stock / daily_demand, 1)
