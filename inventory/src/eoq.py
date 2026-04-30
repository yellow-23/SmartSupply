import math


class EOQModel:
    def __init__(self, demand: float, order_cost: float, holding_cost: float):
        self.demand = demand          # D: demanda anual (unidades)
        self.order_cost = order_cost  # K: costo fijo por pedido (CLP)
        self.holding_cost = holding_cost  # h: costo de almacenamiento unitario anual (CLP)

    def optimal_quantity(self) -> float:
        # Q* = sqrt(2 * D * K / h)
        # TODO: implementar fórmula EOQ
        pass

    def reorder_point(self, daily_demand: float, lead_time: int, service_level: float = 0.95) -> float:
        # s = d̄ * L + z * σ_d * sqrt(L)
        # TODO: calcular punto de reorden con safety stock según nivel de servicio
        pass
