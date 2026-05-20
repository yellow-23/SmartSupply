import React, { useState } from 'react';
import { Play, Download, TrendingUp, Calendar, AlertCircle, Loader2, Info } from 'lucide-react';
import ForecastLineChart from '../components/ForecastLineChart';
import { fetchForecast, fetchSalesHistory, ForecastResponse, SalesPoint } from '../api/forecast';
import { useAuthStore } from '../store/authStore';

const SKU_FAMILIES = [
  'AUTOMOTIVE', 'BABY CARE', 'BEAUTY', 'BEVERAGES', 'BOOKS',
  'BREAD/BAKERY', 'CELEBRATION', 'CLEANING', 'DAIRY', 'DELI',
  'EGGS', 'FROZEN FOODS', 'GROCERY I', 'GROCERY II', 'HARDWARE',
  'HOME AND KITCHEN I', 'HOME AND KITCHEN II', 'HOME APPLIANCES',
  'HOME CARE', 'LADIESWEAR', 'LAWN AND GARDEN', 'LINGERIE',
  'LIQUOR,WINE,BEER', 'MAGAZINES', 'MEATS', 'PERSONAL CARE',
  'PET SUPPLIES', 'PLAYERS AND ELECTRONICS', 'POULTRY',
  'PREPARED FOODS', 'PRODUCE', 'SCHOOL AND OFFICE SUPPLIES', 'SEAFOOD',
];

const MODEL_LABELS: Record<string, string> = {
  xgboost: 'XGBoost',
  arima: 'ARIMA',
  prophet: 'Prophet',
  lstm: 'LSTM',
};

const Forecast = () => {
  const [skuId, setSkuId] = useState('GROCERY I');
  const [storeNbr, setStoreNbr] = useState(1);
  const [horizon, setHorizon] = useState(14);
  const [result, setResult] = useState<ForecastResponse | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const user = useAuthStore(s => s.user);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchForecast({ sku_id: skuId, store_nbr: storeNbr, horizon_days: horizon, model: 'auto' });
      setResult(data);

      // Buscar los 30 dias de historial real previos al inicio de la prediccion
      const firstPredDate = new Date(data.predictions[0].date);
      const histEnd = new Date(firstPredDate);
      histEnd.setDate(histEnd.getDate() - 1);
      const histStart = new Date(histEnd);
      histStart.setDate(histStart.getDate() - 29);

      const toISO = (d: Date) => d.toISOString().split('T')[0];

      let history: SalesPoint[] = [];
      if (user?.business_id) {
        history = await fetchSalesHistory(
          user.business_id, skuId, storeNbr,
          toISO(histStart), toISO(histEnd),
        );
      }

      // Combinar historial y predicciones en un solo arreglo para el grafico
      const histPoints = history.map(h => ({ date: h.date, actual: h.sales }));
      const predPoints = data.predictions.map(p => ({ date: p.date, forecast: p.predicted_sales }));
      setChartData([...histPoints, ...predPoints]);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Error al conectar con el servidor');
    } finally {
      setLoading(false);
    }
  };

  const wapeLabel = result?.mape_validation != null
    ? `${result.mape_validation.toFixed(1)}% de error promedio`
    : 'Sin datos';

  const modelLabel = result ? (MODEL_LABELS[result.model_used] ?? result.model_used.toUpperCase()) : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Predicción de Demanda</h2>
          <p className="text-sm text-gray-500">
            El sistema elige automáticamente el mejor modelo de predicción para cada producto
          </p>
        </div>
        {result && (
          <button className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 transition-all shadow-sm">
            <Download className="w-4 h-4" />
            <span className="text-sm font-medium">Exportar</span>
          </button>
        )}
      </div>

      {/* Filtros */}
      <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex flex-wrap items-center gap-4">
        <div className="flex-1 min-w-[200px]">
          <label className="text-xs text-gray-500 font-medium mb-1 block">Familia de producto</label>
          <select
            className="w-full px-3 py-2 bg-gray-50 rounded-xl text-sm text-gray-700 border-none focus:ring-2 focus:ring-orange-500"
            value={skuId}
            onChange={e => setSkuId(e.target.value)}
          >
            {SKU_FAMILIES.map(f => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>

        <div className="min-w-[120px]">
          <label className="text-xs text-gray-500 font-medium mb-1 block">Tienda</label>
          <input
            type="number"
            min={1}
            max={54}
            className="w-full px-3 py-2 bg-gray-50 rounded-xl text-sm text-gray-700 border-none focus:ring-2 focus:ring-orange-500"
            value={storeNbr}
            onChange={e => setStoreNbr(Number(e.target.value))}
          />
        </div>

        <div className="min-w-[130px]">
          <label className="text-xs text-gray-500 font-medium mb-1 block">Horizonte</label>
          <div className="flex items-center space-x-2 bg-gray-50 px-3 py-2 rounded-xl">
            <Calendar className="w-4 h-4 text-gray-400" />
            <select
              className="bg-transparent border-none text-sm font-medium text-gray-700 focus:ring-0 cursor-pointer"
              value={horizon}
              onChange={e => setHorizon(Number(e.target.value))}
            >
              <option value={7}>7 días</option>
              <option value={14}>14 días</option>
              <option value={30}>30 días</option>
            </select>
          </div>
        </div>

        <div className="flex items-end">
          <button
            onClick={handlePredict}
            disabled={loading}
            className="flex items-center space-x-2 px-5 py-2 bg-orange-600 text-white rounded-xl hover:opacity-90 transition-all disabled:opacity-60"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            <span className="text-sm font-medium">{loading ? 'Calculando...' : 'Predecir'}</span>
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-100 rounded-2xl text-red-700">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Estado inicial */}
      {!result && !loading && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-gray-400 bg-white rounded-2xl border border-gray-100">
          <TrendingUp className="w-12 h-12 mb-3 opacity-30" />
          <p className="text-sm">Selecciona un producto y presiona <strong>Predecir</strong> para ver el pronóstico</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20 text-gray-400 bg-white rounded-2xl border border-gray-100">
          <Loader2 className="w-10 h-10 animate-spin mb-3 text-orange-500" />
          <p className="text-sm font-medium text-gray-600">Entrenando modelos ARIMA, Prophet, XGBoost y LSTM...</p>
          <p className="text-xs text-gray-400 mt-1">Esto puede tomar entre 30 y 90 segundos</p>
        </div>
      )}

      {/* Aviso dataset */}
      <div className="flex items-start gap-3 px-4 py-3 bg-blue-50 border border-blue-100 rounded-xl text-blue-700 text-sm">
        <Info className="w-4 h-4 mt-0.5 shrink-0" />
        <span>
          Los datos corresponden al dataset de benchmarking <strong>Corporación Favorita (2013–2017)</strong>.
          Una vez que importes tus propios datos desde <strong>Importar datos</strong>, el sistema usará tu historial real.
        </span>
      </div>

      {/* Resultados */}
      {result && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-[420px]">
            <ForecastLineChart
              data={chartData}
              title={`Pronóstico de ventas — ${result.sku_id} · Tienda ${result.store_nbr}`}
            />
          </div>

          <div className="space-y-4">
            {/* Tarjeta modelo ganador */}
            <div className="bg-gradient-to-br from-slate-950 to-blue-900 p-6 rounded-2xl text-white shadow-xl relative overflow-hidden">
              <TrendingUp className="absolute -right-4 -bottom-4 w-32 h-32 text-white/5 rotate-12" />
              <p className="text-blue-200 text-xs font-bold uppercase tracking-widest mb-2">Mejor Modelo (AMS)</p>
              <h4 className="text-3xl font-bold mb-1">{modelLabel}</h4>
              <p className="text-blue-100 text-sm opacity-80">{wapeLabel}</p>
              <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-between">
                <span className="text-xs text-blue-200">{result.horizon_days} días predichos</span>
                <span className="px-2 py-1 bg-green-500/20 text-green-300 text-[10px] font-bold rounded uppercase">Seleccionado</span>
              </div>
            </div>

            {/* Resumen para el cliente */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 space-y-3">
              <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide">Resumen del pronóstico</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Producto</span>
                  <span className="font-semibold text-gray-800">{result.sku_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Tienda</span>
                  <span className="font-semibold text-gray-800">#{result.store_nbr}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Periodo</span>
                  <span className="font-semibold text-gray-800">{result.predictions[0]?.date} → {result.predictions.at(-1)?.date}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Total estimado</span>
                  <span className="font-bold text-orange-600">
                    {result.predictions.reduce((s, p) => s + p.predicted_sales, 0).toLocaleString('es-CL', { maximumFractionDigits: 0 })} uds
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Promedio diario</span>
                  <span className="font-semibold text-gray-800">
                    {(result.predictions.reduce((s, p) => s + p.predicted_sales, 0) / result.predictions.length).toLocaleString('es-CL', { maximumFractionDigits: 0 })} uds/día
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Precisión del modelo</span>
                  <span className={`font-bold ${(result.mape_validation ?? 100) < 20 ? 'text-green-600' : (result.mape_validation ?? 100) < 40 ? 'text-yellow-600' : 'text-red-500'}`}>
                    {result.mape_validation != null ? `${(100 - result.mape_validation).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Forecast;
