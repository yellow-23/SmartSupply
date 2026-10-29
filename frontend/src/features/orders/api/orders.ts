import api from '../../../shared/api/axios.instance'

export interface PurchaseOrderLine {
  id: number
  family: string
  quantity: number
  unit_cost: number | null
  trigger_stock: number | null
  reorder_point_s: number | null
  order_up_to_S: number | null
}

export interface PurchaseOrder {
  id: number
  order_number: string
  business_id: number
  store_nbr: number
  supplier: string | null
  policy_used: string
  status: 'pending' | 'confirmed' | 'in_transit' | 'received' | 'cancelled'
  created_at: string
  expected_delivery: string | null
  received_at: string | null
  lines: PurchaseOrderLine[]
  total_cost: number | null
}

export interface OrderFilters {
  store_nbr?: string
  status?: string
  q?: string
  date_from?: string
  date_to?: string
}

const filterParams = (businessId: number, f: OrderFilters) => {
  const params = new URLSearchParams({ business_id: String(businessId) })
  for (const [k, v] of Object.entries(f)) if (v) params.set(k, v)
  return params
}

export const fetchOrders = (businessId: number, filters: OrderFilters = {}) =>
  api.get<PurchaseOrder[]>(`/orders?${filterParams(businessId, filters)}`).then(r => r.data)

export const generateOrders = (businessId: number, storeNbr = 1) =>
  api.post<PurchaseOrder[]>(
    `/orders/generate?business_id=${businessId}&store_nbr=${storeNbr}`
  ).then(r => r.data)

export const updateOrderStatus = (orderId: number, businessId: number, newStatus: string) =>
  api.patch<PurchaseOrder>(
    `/orders/${orderId}/status?business_id=${businessId}&new_status=${newStatus}`
  ).then(r => r.data)

export const exportOrders = (businessId: number, filters: OrderFilters = {}) =>
  api.get(`/orders/export?${filterParams(businessId, filters)}`, { responseType: 'blob' }).then(r => r.data as Blob)

export interface OrderLineInput {
  family: string
  quantity: number
  unit_cost?: number | null
}

export interface OrderInput {
  supplier?: string | null
  expected_delivery?: string | null
  lines: OrderLineInput[]
}

export const createOrder = (businessId: number, storeNbr: number, body: OrderInput) =>
  api.post<PurchaseOrder>('/orders', { ...body, business_id: businessId, store_nbr: storeNbr }).then(r => r.data)

export const updateOrder = (orderId: number, businessId: number, body: OrderInput) =>
  api.patch<PurchaseOrder>(`/orders/${orderId}?business_id=${businessId}`, body).then(r => r.data)

export const downloadOrderPdf = (orderId: number, businessId: number) =>
  api.get(`/orders/${orderId}/pdf?business_id=${businessId}`, { responseType: 'blob' }).then(r => r.data as Blob)
