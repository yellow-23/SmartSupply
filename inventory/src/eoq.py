import math

import numpy as np
from scipy import stats


class EOQModel:
    """
    Modelo EOQ clásico con stock de seguridad basado en nivel de servicio.

    Parámetros
    ----------
    demand       : D — demanda anual estimada (unidades).
    order_cost   : K — costo fijo por pedido (CLP).
    holding_cost : h — costo de almacenamiento unitario anual (CLP/ud/año).
    """

    def __init__(self, demand: float, order_cost: float, holding_cost: float):
        self.demand = demand
        self.order_cost = order_cost
        self.holding_cost = holding_cost

    def optimal_quantity(self) -> float:
        """
        Q* = sqrt(2 * D * K / h)

        Retorna 0 si los parámetros no son positivos.
        """
        if self.holding_cost <= 0 or self.demand <= 0 or self.order_cost <= 0:
            return 0.0
        return math.sqrt(2 * self.demand * self.order_cost / self.holding_cost)

    def safety_stock(
        self, daily_std: float, lead_time: int, service_level: float = 0.95
    ) -> float:
        """
        SS = z * σ_d * sqrt(L)

        Parámetros
        ----------
        daily_std     : desviación estándar de la demanda diaria.
        lead_time     : tiempo de entrega del proveedor (días).
        service_level : probabilidad de no ruptura de stock (0–1).
        """
        z = float(stats.norm.ppf(service_level))
        return z * daily_std * math.sqrt(lead_time)

    def reorder_point(
        self,
        daily_demand: float,
        lead_time: int,
        daily_std: float | None = None,
        service_level: float = 0.95,
    ) -> float:
        """
        s = d̄ * L + SS

        Parámetros
        ----------
        daily_demand : demanda media diaria.
        lead_time    : tiempo de entrega (días).
        daily_std    : desviación estándar de demanda diaria (opcional).
        service_level: nivel de servicio deseado (por defecto 95 %).
        """
        ss = (
            self.safety_stock(daily_std, lead_time, service_level)
            if daily_std is not None
            else 0.0
        )
        return daily_demand * lead_time + ss
