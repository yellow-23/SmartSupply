import api from './axios.instance'

export interface InventoryAlert {
  family: string
  current_stock: number
  reorder_point_s: number
  order_up_to_S: number
  order_quantity: number
  urgency: 'critical' | 'high' | 'normal'
}

export interface InventoryStatus {
  sku_id: string
  store_nbr: number
  current_stock: number
  reorder_point_s: number
  order_up_to_S: number
  eoq: number
  policy: string
  needs_reorder: boolean
  days_until_stockout: number | null
  updated_at: string
}

export interface InventoryMetrics {
  sku_id: string
  store_nbr: number
  period_start: string
  period_end: string
  capital_inmovilizado: number
  stockout_rate: number
  inventory_turnover: number
  service_level: number
  total_inventory_cost: number
}

export interface PurchaseOrder {
  id: number
  business_id: number
  store_nbr: number
  family: string
  quantity: number
  trigger_stock: number | null
  reorder_point_s: number | null
  order_up_to_S: number | null
  policy_used: string
  status: 'pending' | 'confirmed' | 'in_transit' | 'received' | 'cancelled'
  created_at: string
  expected_delivery: string | null
  received_at: string | null
}

export const fetchAlerts = (businessId: number, storeNbr = 1) =>
  api.get<{ alerts: InventoryAlert[]; count: number; has_clp_skus: boolean }>(
    `/inventory/alerts?business_id=${businessId}&store_nbr=${storeNbr}`
  ).then(r => r.data)

export const fetchInventoryStatus = (family: string, businessId: number, storeNbr = 1) =>
  api.get<InventoryStatus>(
    `/inventory/${encodeURIComponent(family)}?business_id=${businessId}&store_nbr=${storeNbr}`
  ).then(r => r.data)

export const fetchInventoryMetrics = (family: string, businessId: number, storeNbr = 1, periodDays = 30) =>
  api.get<InventoryMetrics>(
    `/inventory/${encodeURIComponent(family)}/metrics?business_id=${businessId}&store_nbr=${storeNbr}&period_days=${periodDays}`
  ).then(r => r.data)

export const fetchOrders = (businessId: number, storeNbr = 1, status?: string) => {
  const params = new URLSearchParams({ business_id: String(businessId), store_nbr: String(storeNbr) })
  if (status) params.set('status', status)
  return api.get<PurchaseOrder[]>(`/orders?${params}`).then(r => r.data)
}

export const generateOrders = (businessId: number, storeNbr = 1) =>
  api.post<PurchaseOrder[]>(
    `/orders/generate?business_id=${businessId}&store_nbr=${storeNbr}`
  ).then(r => r.data)

export const updateOrderStatus = (orderId: number, businessId: number, newStatus: string) =>
  api.patch<PurchaseOrder>(
    `/orders/${orderId}/status?business_id=${businessId}&new_status=${newStatus}`
  ).then(r => r.data)
