import client from '../../../shared/api/client';

export interface SalesPoint {
  date: string;
  sales: number;
}

export async function fetchSalesHistory(
  businessId: number,
  family: string,
  storeNbr: number,
  start: string,
  end: string,
): Promise<SalesPoint[]> {
  const { data } = await client.get<SalesPoint[]>('/sales/history', {
    params: { business_id: businessId, family, store_nbr: storeNbr, start, end },
  });
  return data;
}

export interface ForecastPoint {
  date: string;
  predicted_sales: number;
}

export interface ForecastResponse {
  sku_id: string;
  store_nbr: number;
  model_used: string;
  mape_validation: number | null;
  horizon_days: number;
  predictions: ForecastPoint[];
  generated_at: string;
  sales_unit: "CLP" | "units";
}

export interface ForecastRequest {
  sku_id: string;
  store_nbr: number;
  horizon_days: number;
  model?: string;
}

export interface ForecastStoreOption {
  store_nbr: number;
  name: string;
  days_available: number;
}

export interface ForecastOptions {
  families: string[];
  stores: ForecastStoreOption[];
  days_required: number;
}

export interface InsufficientDataDetail {
  code: 'insufficient_data';
  days_available: number;
  days_required: number;
  message: string;
}

export async function fetchForecast(req: ForecastRequest): Promise<ForecastResponse> {
  const { data } = await client.post<ForecastResponse>('/forecast/predict', req);
  return data;
}

export async function fetchForecastOptions(): Promise<ForecastOptions> {
  const { data } = await client.get<ForecastOptions>('/forecast/options');
  return data;
}

export function isInsufficientDataError(err: any): err is { response: { data: { detail: InsufficientDataDetail } } } {
  return err?.response?.status === 422 && err?.response?.data?.detail?.code === 'insufficient_data';
}

export async function exportForecastPdf(req: ForecastRequest): Promise<Blob> {
  const { data } = await client.get(`/forecast/${encodeURIComponent(req.sku_id)}/export`, {
    params: { store_nbr: req.store_nbr, horizon_days: req.horizon_days, model: req.model },
    responseType: 'blob',
  });
  return data as Blob;
}
