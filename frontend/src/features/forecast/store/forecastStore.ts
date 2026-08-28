import { create } from 'zustand';
import { ForecastResponse } from '../api/forecast';

interface ForecastState {
  skuId: string;
  storeNbr: number | null;
  horizon: number;
  result: ForecastResponse | null;
  chartData: any[];
  error: string | null;

  setSkuId: (id: string) => void;
  setStoreNbr: (n: number | null) => void;
  setHorizon: (h: number) => void;
  setResult: (r: ForecastResponse | null) => void;
  setChartData: (d: any[]) => void;
  setError: (e: string | null) => void;
}

export const useForecastStore = create<ForecastState>()((set) => ({
  skuId: '',
  storeNbr: null,
  horizon: 14,
  result: null,
  chartData: [],
  error: null,

  setSkuId: (skuId) => set({ skuId }),
  setStoreNbr: (storeNbr) => set({ storeNbr }),
  setHorizon: (horizon) => set({ horizon }),
  setResult: (result) => set({ result }),
  setChartData: (chartData) => set({ chartData }),
  setError: (error) => set({ error }),
}));
