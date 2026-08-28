import api from "../../../shared/api/axios.instance";

export interface Product {
  id: number;
  business_id: number;
  store_nbr: number;
  family: string;
  unit_cost: number | null;
  order_cost: number;
  holding_rate: number;
  lead_time_days: number;
  moq: number | null;
  created_at: string;
}

export interface ProductCreate {
  business_id: number;
  store_nbr: number;
  family: string;
  unit_cost?: number | null;
  order_cost?: number;
  holding_rate?: number;
  lead_time_days?: number;
  moq?: number | null;
}

export interface ProductUpdate {
  unit_cost?: number | null;
  order_cost?: number;
  holding_rate?: number;
  lead_time_days?: number;
  moq?: number | null;
}

export interface ProductPage {
  items: Product[];
  total: number;
  page: number;
  pages: number;
  total_families: number;
}

export async function fetchProducts(params?: {
  business_id?: number;
  store_nbr?: number;
  family?: string;
  page?: number;
  limit?: number;
}): Promise<ProductPage> {
  const { data } = await api.get("/products", { params });
  return data;
}

export async function createProduct(body: ProductCreate): Promise<Product> {
  const { data } = await api.post("/products/", body);
  return data;
}

export async function updateProduct(id: number, body: ProductUpdate): Promise<Product> {
  const { data } = await api.patch(`/products/${id}`, body);
  return data;
}

export async function deleteProduct(id: number): Promise<void> {
  await api.delete(`/products/${id}`);
}
