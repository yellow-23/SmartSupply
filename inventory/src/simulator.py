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
        stock = initial_stock if initial_stock > 0 else S
        pending_orders = []  # list of (arrival_day, quantity)
        stock_history = []
        orders_qty = []

        demand_values = demand.values
        n = len(demand_values)

        for t in range(n):
            # Receive orders arriving today
            still_pending = []
            for (arrival_day, qty) in pending_orders:
                if arrival_day == t:
                    stock += qty
                else:
                    still_pending.append((arrival_day, qty))
            pending_orders = still_pending

            # Consume demand
            stock -= demand_values[t]

            # Emit order if stock <= s and no pending orders
            if stock <= s and len(pending_orders) == 0:
                order_qty = S - stock
                if order_qty > 0:
                    pending_orders.append((t + lead_time, order_qty))
                    orders_qty.append(order_qty)

            stock_history.append(stock)

        stock_arr = np.array(stock_history)
        total_demand = float(demand_values.sum())

        # Avoid division by zero when demand is all zeros
        positive_stock = stock_arr[stock_arr > 0]
        avg_positive_stock = float(positive_stock.mean()) if len(positive_stock) > 0 else 0.0

        capital_inmovilizado = avg_positive_stock * self.unit_cost

        stockout_days = int((stock_arr < 0).sum())
        stockout_rate = stockout_days / n if n > 0 else 0.0
        service_level = 1.0 - stockout_rate

        inventory_turnover = (total_demand / avg_positive_stock) if avg_positive_stock > 0 else 0.0

        holding_cost = float(np.maximum(stock_arr, 0).sum()) * self.unit_cost * self.holding_rate / 365
        num_orders = len(orders_qty)
        ordering_cost = num_orders * self.order_cost
        total_inventory_cost = holding_cost + ordering_cost

        avg_order_quantity = float(np.mean(orders_qty)) if orders_qty else 0.0

        return {
            "capital_inmovilizado": capital_inmovilizado,
            "stockout_rate": stockout_rate,
            "inventory_turnover": inventory_turnover,
            "service_level": service_level,
            "total_inventory_cost": total_inventory_cost,
            "num_orders": num_orders,
            "avg_order_quantity": avg_order_quantity,
        }
