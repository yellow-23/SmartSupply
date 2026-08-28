import api from '../../../shared/api/axios.instance'

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

export const exportOrders = (businessId: number, storeNbr = 1, status?: string) => {
  const params = new URLSearchParams({ business_id: String(businessId), store_nbr: String(storeNbr) })
  if (status) params.set('status', status)
  return api.get(`/orders/export?${params}`, { responseType: 'blob' }).then(r => r.data as Blob)
}
