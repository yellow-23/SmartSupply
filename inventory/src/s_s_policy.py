import numpy as np


class SsPolicyModel:
    """
    Política (s, S) dinámica alimentada por predicciones del módulo de forecasting.
    - s: punto de reorden (si stock <= s → generar orden)
    - S: nivel de reposición (ordenar hasta S)
    """

    def __init__(self, lead_time: int, holding_cost: float, order_cost: float):
        self.lead_time = lead_time
        self.holding_cost = holding_cost
        self.order_cost = order_cost

    def calculate_s(self, forecast: np.ndarray, service_level: float = 0.95) -> float:
        # s = demanda pronosticada durante lead_time + safety stock
        # TODO: implementar usando predicciones del módulo forecasting/
        pass

    def calculate_S(self, s: float, eoq: float) -> float:
        # S = s + Q*
        # TODO: implementar respetando restricciones del proveedor (MOQ, pack size)
        pass

    def needs_reorder(self, current_stock: float, s: float) -> bool:
        return current_stock <= s

    def order_quantity(self, current_stock: float, S: float) -> float:
        return max(0, S - current_stock)
