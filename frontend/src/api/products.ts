import api from "./axios.instance";

export interface Product {
  id: number;
  sku_id: string;
  name: string;
  family: string;
  store_nbr: number;
  unit_cost: number;
  lead_time_days: number;
  min_order_qty: number;
  created_at: string;
}

export interface ProductCreate {
  sku_id: string;
  name: string;
  family: string;
  store_nbr: number;
  unit_cost: number;
  lead_time_days: number;
  min_order_qty: number;
}

export interface ProductUpdate {
  name?: string;
  family?: string;
  unit_cost?: number;
  lead_time_days?: number;
  min_order_qty?: number;
}

export async function fetchProducts(params?: {
  store_nbr?: number;
  family?: string;
  search?: string;
}): Promise<Product[]> {
  const { data } = await api.get("/products/", { params });
  return data;
}

export async function createProduct(body: ProductCreate): Promise<Product> {
  const { data } = await api.post("/products/", body);
  return data;
}

export async function updateProduct(id: number, body: ProductUpdate): Promise<Product> {
  const { data } = await api.put(`/products/${id}`, body);
  return data;
}

export async function deleteProduct(id: number): Promise<void> {
  await api.delete(`/products/${id}`);
}
