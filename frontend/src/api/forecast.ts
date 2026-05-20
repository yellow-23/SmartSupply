import client from './client';

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
}

export interface ForecastRequest {
  sku_id: string;
  store_nbr: number;
  horizon_days: number;
  model?: string;
}

export async function fetchForecast(req: ForecastRequest): Promise<ForecastResponse> {
  const { data } = await client.post<ForecastResponse>('/forecast/predict', req);
  return data;
}
