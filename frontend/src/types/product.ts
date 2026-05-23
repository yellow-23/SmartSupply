export interface ProductResponse {
  id: number;
  sku_id: string;
  name: string;
  family: string;
  store_nbr: number;
  unit_cost: number;
  lead_time_days: number;
  order_cost: number;
  holding_cost_pct: number;
  min_order_qty: number;
  pack_size: number;
  supplier_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductPage {
  items: ProductResponse[];
  total: number;
  page: number;
  pages: number;
  total_active: number;
  total_inactive: number;
  total_families: number;
}
