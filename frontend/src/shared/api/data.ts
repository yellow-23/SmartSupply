// frontend/src/api/data.ts
import api from "./axios.instance";

export interface Business {
  id: number;
  name: string;
  rut: string | null;
  city: string | null;
  type: string | null;
  owner_user_id: number | null;
  created_at: string;
}

export interface StoreItem {
  store_nbr: number;
  city: string | null;
  state: string | null;
  type: string | null;
  cluster: number | null;
}

export interface IngestLogItem {
  id: number;
  business_id: number;
  store_nbr: number;
  user_id: number;
  uploader_name: string | null;
  filename: string;
  file_type: string;
  records_loaded: number;
  sales_unit: string;
  date_range_start: string | null;
  date_range_end: string | null;
  families: string[] | null;
  status: string;
  created_at: string;
}

export interface SalesRecord {
  id: number;
  date: string;
  family: string;
  sales: number;
  onpromotion: number;
  sales_unit: string;
  ingest_id: number | null;
}

export async function listBusinesses(): Promise<Business[]> {
  const { data } = await api.get("/businesses");
  return data;
}

export async function createBusiness(payload: {
  name: string; rut?: string; city?: string; type?: string;
}): Promise<Business> {
  const { data } = await api.post("/businesses", payload);
  return data;
}

export async function listBusinessStores(businessId: number): Promise<StoreItem[]> {
  const { data } = await api.get(`/businesses/${businessId}/stores`);
  return data;
}

export async function listIngests(businessId: number, storeNbr?: number): Promise<IngestLogItem[]> {
  const params: Record<string, number> = { business_id: businessId };
  if (storeNbr != null) params.store_nbr = storeNbr;
  const { data } = await api.get("/ingests", { params });
  return data;
}

export async function getIngestRecords(ingestId: number): Promise<SalesRecord[]> {
  const { data } = await api.get(`/ingests/${ingestId}`);
  return data;
}

export async function revertIngest(ingestId: number): Promise<IngestLogItem> {
  const { data } = await api.post(`/ingests/${ingestId}/revert`);
  return data;
}

export async function deleteIngest(ingestId: number): Promise<void> {
  await api.delete(`/ingests/${ingestId}`);
}

export async function updateRecord(
  recordId: number,
  patch: Partial<Pick<SalesRecord, "date" | "family" | "sales" | "onpromotion">>,
): Promise<SalesRecord> {
  const { data } = await api.patch(`/sales/record/${recordId}`, patch);
  return data;
}

export async function deleteRecord(recordId: number): Promise<void> {
  await api.delete(`/sales/record/${recordId}`);
}
