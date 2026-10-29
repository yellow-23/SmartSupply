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

// business_id=1 es el dataset de referencia Favorita (CU-27)
export const BENCHMARK_BUSINESS_ID = 1;

export interface ForecastRequest {
  business_id: number | null;
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
  categories: Record<string, string>;
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
  const { business_id, ...body } = req;
  const { data } = await client.post<ForecastResponse>('/forecast/predict', body, { params: { business_id } });
  return data;
}

export async function fetchForecastOptions(businessId: number | null): Promise<ForecastOptions> {
  const { data } = await client.get<ForecastOptions>('/forecast/options', { params: { business_id: businessId } });
  return data;
}

export function isInsufficientDataError(err: any): err is { response: { data: { detail: InsufficientDataDetail } } } {
  return err?.response?.status === 422 && err?.response?.data?.detail?.code === 'insufficient_data';
}

export interface ForecastAccuracyItem {
  family: string;
  store_nbr: number;
  evaluated_days: number;
  wape_actual: number | null;
  avg_predicted: number;
  avg_actual: number;
  last_model_used: string;
}

export async function fetchForecastAccuracy(businessId: number, storeNbr?: number): Promise<ForecastAccuracyItem[]> {
  const { data } = await client.get<ForecastAccuracyItem[]>('/forecast/accuracy', {
    params: { business_id: businessId, store_nbr: storeNbr },
  });
  return data;
}

export type ExportFormat = 'pdf' | 'xlsx';

// Manda la prediccion que se esta viendo: el backend arma el archivo sin depender de su cache
export async function exportForecast(result: ForecastResponse, businessId: number | null, format: ExportFormat): Promise<Blob> {
  const { data } = await client.post('/forecast/export', result, {
    params: { format, business_id: businessId },
    responseType: 'blob',
  });
  return data as Blob;
}

export async function exportStoreForecast(businessId: number | null, storeNbr: number, horizon: number, format: ExportFormat): Promise<Blob> {
  const { data } = await client.get('/dashboard/store-forecast/export', {
    params: { business_id: businessId, store_nbr: storeNbr, horizon_days: horizon, format },
    responseType: 'blob',
  });
  return data as Blob;
}

export const exportFileName = (subject: string, format: ExportFormat) =>
  `prediccion_${subject.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '')}_${new Date().toISOString().slice(0, 10)}.${format}`;
