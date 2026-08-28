import { useEffect, useMemo, useState } from 'react';
import { Play, Download, TrendingUp, Calendar, AlertCircle, Loader2, Upload } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import ForecastLineChart from '../components/ForecastLineChart';
import {
  fetchForecast,
  fetchForecastOptions,
  exportForecastPdf,
  fetchSalesHistory,
  isInsufficientDataError,
  SalesPoint,
} from '../api/forecast';
import { useAuthStore } from '../../auth/store/authStore';
import { useForecastStore } from '../store/forecastStore';
import { downloadBlob } from '../../../shared/lib/utils';

const MODEL_LABELS: Record<string, string> = {
  xgboost: 'XGBoost',
  arima: 'ARIMA',
  prophet: 'Prophet',
  lstm: 'LSTM',
};

const Forecast = () => {
  const navigate = useNavigate();
  const user = useAuthStore(s => s.user);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const {
    skuId, setSkuId,
    storeNbr, setStoreNbr,
    horizon, setHorizon,
    result, setResult,
    chartData, setChartData,
    error, setError,
  } = useForecastStore();

  const {
    data: options,
    isLoading: optionsLoading,
  } = useQuery({
    queryKey: ['forecast', 'options'],
    queryFn: fetchForecastOptions,
    staleTime: 60_000,
  });

  // Inicializar selección con la primera familia/tienda disponibles
  useEffect(() => {
    if (!options) return;
    if (!skuId && options.families.length > 0) setSkuId(options.families[0]);
    if (storeNbr == null && options.stores.length > 0) setStoreNbr(options.stores[0].store_nbr);
  }, [options]);

  const selectedStore = useMemo(
    () => options?.stores.find(s => s.store_nbr === storeNbr) ?? null,
    [options, storeNbr],
  );
  const daysAvailable = selectedStore?.days_available ?? 0;
  const daysRequired = options?.days_required ?? 90;
  const hasEnoughData = daysAvailable >= daysRequired;
  const hasAnyData = !!options && options.families.length > 0 && options.stores.length > 0;

  const handleExport = async () => {
    if (!skuId || storeNbr == null) return;
    setExporting(true);
    try {
      const blob = await exportForecastPdf({ sku_id: skuId, store_nbr: storeNbr, horizon_days: horizon, model: 'auto' });
      downloadBlob(blob, `forecast_${skuId}_${storeNbr}.pdf`);
    } finally {
      setExporting(false);
    }
  };

  const handlePredict = async () => {
    if (!skuId || storeNbr == null) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await fetchForecast({ sku_id: skuId, store_nbr: storeNbr, horizon_days: horizon, model: 'auto' });
      setResult(data);

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

      const histPoints = history.map(h => ({ date: h.date, actual: h.sales }));
      const predPoints = data.predictions.map(p => ({ date: p.date, forecast: p.predicted_sales }));
      setChartData([...histPoints, ...predPoints]);
    } catch (e: any) {
      if (isInsufficientDataError(e)) {
        setError(e.response.data.detail.message);
      } else {
        setError(e?.response?.data?.detail ?? 'Error al conectar con el servidor');
      }
    } finally {
      setLoading(false);
    }
  };

  const wapeLabel = result?.mape_validation != null
    ? `${result.mape_validation.toFixed(1)}% de error promedio`
    : 'Sin datos';

  const modelLabel = result ? (MODEL_LABELS[result.model_used] ?? result.model_used.toUpperCase()) : null;
  const isCLP = result?.sales_unit === 'CLP';
  const unitLabel = isCLP ? 'CLP' : 'uds';
  const formatValue = (v: number) =>
    isCLP
      ? `$${v.toLocaleString('es-CL', { maximumFractionDigits: 0 })}`
      : v.toLocaleString('es-CL', { maximumFractionDigits: 0 });

  // ─── Estado: cargando opciones ────────────────────────────────────────────
  if (optionsLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-400 bg-white rounded-2xl border border-gray-100">
        <Loader2 className="w-10 h-10 animate-spin mb-3 text-orange-500" />
        <p className="text-sm">Cargando tus datos...</p>
      </div>
    );
  }

  // ─── Estado: sin datos ────────────────────────────────────────────────────
  if (!hasAnyData) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 p-12 flex flex-col items-center text-center space-y-5">
        <div className="w-16 h-16 bg-orange-50 rounded-2xl flex items-center justify-center">
          <Upload className="w-8 h-8 text-orange-600" />
        </div>
        <div className="space-y-2 max-w-md">
          <h2 className="text-2xl font-bold text-gray-800">Aún no tienes ventas cargadas</h2>
          <p className="text-gray-500 text-sm">
            Para predecir tu demanda necesito conocer tu historial. Sube tus primeros datos y Stocky los va a ordenar por ti.
          </p>
        </div>
        <button
          onClick={() => navigate('/ingest')}
          className="px-6 py-3 bg-orange-600 text-white rounded-xl font-semibold hover:opacity-90 transition-all"
        >
          Subir mis ventas
        </button>
      </div>
    );
  }

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
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 transition-all shadow-sm disabled:opacity-60"
          >
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            <span className="text-sm font-medium">Exportar PDF</span>
          </button>
        )}
      </div>

      {/* Filtros */}
      <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex flex-wrap items-center gap-4">
        <div className="flex-1 min-w-[200px]">
          <label className="text-xs text-gray-500 font-medium mb-1 block">Producto</label>
          <select
            className="w-full px-3 py-2 bg-gray-50 rounded-xl text-sm text-gray-700 border-none focus:ring-2 focus:ring-orange-500"
            value={skuId}
            onChange={e => setSkuId(e.target.value)}
          >
            {options!.families.map(f => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>

        <div className="min-w-[200px]">
          <label className="text-xs text-gray-500 font-medium mb-1 block">Tienda</label>
          <select
            className="w-full px-3 py-2 bg-gray-50 rounded-xl text-sm text-gray-700 border-none focus:ring-2 focus:ring-orange-500"
            value={storeNbr ?? ''}
            onChange={e => setStoreNbr(Number(e.target.value))}
          >
            {options!.stores.map(s => (
              <option key={s.store_nbr} value={s.store_nbr}>
                {s.name} ({s.days_available} días)
              </option>
            ))}
          </select>
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
            disabled={loading || !hasEnoughData}
            className="flex items-center space-x-2 px-5 py-2 bg-orange-600 text-white rounded-xl hover:opacity-90 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            <span className="text-sm font-medium">{loading ? 'Calculando...' : 'Predecir'}</span>
          </button>
        </div>
      </div>

      {/* Banner pocos datos */}
      {!hasEnoughData && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-5 py-4 bg-amber-50 border border-amber-200 rounded-2xl">
          <div className="flex items-start gap-3 text-amber-800">
            <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
            <div className="text-sm">
              <p className="font-semibold">Necesitas más historial para predecir.</p>
              <p className="text-amber-700">
                Llevas <strong>{daysAvailable} días</strong> cargados en esta tienda. Te faltan <strong>{Math.max(daysRequired - daysAvailable, 0)} días</strong> para activar el pronóstico.
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/ingest')}
            className="shrink-0 px-4 py-2 bg-amber-600 text-white text-sm rounded-xl font-semibold hover:opacity-90 transition-all"
          >
            Subir más ventas
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-100 rounded-2xl text-red-700">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Estado inicial (con datos suficientes pero sin haber predicho aún) */}
      {!result && !loading && !error && hasEnoughData && (
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
                    {formatValue(result.predictions.reduce((s, p) => s + p.predicted_sales, 0))} {unitLabel}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Promedio diario</span>
                  <span className="font-semibold text-gray-800">
                    {formatValue(result.predictions.reduce((s, p) => s + p.predicted_sales, 0) / result.predictions.length)} {unitLabel}/día
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
