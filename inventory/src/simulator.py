import numpy as np
import pandas as pd


class InventorySimulator:
    """
    Simulador de políticas de inventario.
    Permite comparar EOQ vs (s,S) sobre el mismo dataset de demanda real
    midiendo: capital inmovilizado, tasa de quiebre, rotación, nivel de servicio y CTI.
    """

    def __init__(self, unit_cost: float, holding_rate: float = 0.25, order_cost: float = 5000.0):
        self.unit_cost = unit_cost        # Costo unitario de adquisición (CLP)
        self.holding_rate = holding_rate  # Tasa de costo de mantener inventario (% anual)
        self.order_cost = order_cost      # Costo fijo por pedido (CLP)

    def run(self, demand: pd.Series, policy: str, s: float, S: float, initial_stock: float, lead_time: int) -> dict:
        """
        Simula la política sobre la serie de demanda real y retorna métricas.

        Args:
            demand: Serie de demanda diaria real (período de prueba)
            policy: 'eoq' o 's_s'
            s: punto de reorden
            S: nivel de reposición
            initial_stock: stock inicial de la simulación
            lead_time: días entre emisión y recepción del pedido

        Returns:
            dict con capital_inmovilizado, stockout_rate, inventory_turnover,
                 service_level, total_inventory_cost
        """
        # TODO: implementar simulación día a día
        # Para cada día: descontar demanda, verificar si stock <= s, emitir orden, recibir pedidos
        pass
