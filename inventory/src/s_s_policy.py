import math

import numpy as np
from scipy import stats


class SsPolicyModel:
    """
    Política (s, S) dinámica alimentada por predicciones del módulo de forecasting.

    - s : punto de reorden — si stock ≤ s se genera una orden.
    - S : nivel de reposición — se ordena hasta S unidades.
    """

    def __init__(self, lead_time: int, holding_cost: float, order_cost: float):
        self.lead_time = lead_time
        self.holding_cost = holding_cost
        self.order_cost = order_cost

    def calculate_s(
        self, forecast: np.ndarray, service_level: float = 0.95
    ) -> float:
        """
        s = demanda pronosticada durante lead_time + stock de seguridad.

        Parámetros
        ----------
        forecast      : array de predicciones diarias del módulo forecasting.
        service_level : nivel de servicio deseado (por defecto 95 %).
        """
        forecast = np.asarray(forecast, dtype=float)
        daily_demand = float(np.mean(forecast))
        daily_std = float(np.std(forecast, ddof=1)) if len(forecast) > 1 else 0.0
        z = float(stats.norm.ppf(service_level))
        safety_stock = z * daily_std * math.sqrt(self.lead_time)
        return daily_demand * self.lead_time + safety_stock

    def calculate_S(self, s: float, eoq: float) -> float:
        """S = s + Q*"""
        return s + eoq

    def needs_reorder(self, current_stock: float, s: float) -> bool:
        return current_stock <= s

    def order_quantity(self, current_stock: float, S: float) -> float:
        return max(0.0, S - current_stock)
