import api from '../../../shared/api/axios.instance'

export interface InventoryAlert {
  family: string
  current_stock: number
  reorder_point_s: number
  order_up_to_S: number | null
  order_quantity: number | null
  needs_cost_setup: boolean
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

export const exportAlerts = (businessId: number, storeNbr = 1) =>
  api.get(`/inventory/alerts/export?business_id=${businessId}&store_nbr=${storeNbr}`, { responseType: 'blob' })
    .then(r => r.data as Blob)
