import React, { useState } from 'react';
import { Search, Play, Download, Filter, TrendingUp, Calendar } from 'lucide-react';
import ForecastLineChart from '../components/ForecastLineChart';
import ModelComparisonTable from '../components/ModelComparisonTable';

const Forecast = () => {
  const [selectedSku, setSelectedSku] = useState('GROCERY-001');
  const [horizon, setHorizon] = useState(14);

  const mockData = [
    { date: '2025-05-01', actual: 45, forecast: 44, lower: 40, upper: 48 },
    { date: '2025-05-02', actual: 52, forecast: 50, lower: 45, upper: 55 },
    { date: '2025-05-03', actual: 48, forecast: 49, lower: 44, upper: 54 },
    { date: '2025-05-04', actual: 61, forecast: 58, lower: 53, upper: 63 },
    { date: '2025-05-05', forecast: 55, lower: 50, upper: 60 },
    { date: '2025-05-06', forecast: 57, lower: 52, upper: 62 },
    { date: '2025-05-07', forecast: 54, lower: 49, upper: 59 },
    { date: '2025-05-08', forecast: 59, lower: 54, upper: 64 },
  ];

  const mockModels = [
    { name: 'Prophet', mape: 8.32, rmse: 4.12, bias: -0.15, status: 'best' as const },
    { name: 'XGBoost', mape: 9.45, rmse: 5.21, bias: +0.42, status: 'default' as const },
    { name: 'ARIMA', mape: 11.20, rmse: 6.80, bias: -1.05, status: 'default' as const },
    { name: 'LSTM', mape: 12.15, rmse: 7.45, bias: +0.88, status: 'default' as const },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Predicción de Demanda</h2>
          <p className="text-sm text-gray-500">El sistema elige automáticamente el mejor modelo de predicción para cada producto</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 transition-all shadow-sm">
            <Download className="w-4 h-4" />
            <span className="text-sm font-medium">Exportar</span>
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-orange-600 text-white rounded-xl hover:opacity-90 transition-all">
            <Play className="w-4 h-4" />
            <span className="text-sm font-medium">Actualizar predicciones</span>
          </button>
        </div>
      </div>

      <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input 
            type="text" 
            placeholder="Buscar producto o categoría..."
            className="w-full pl-10 pr-4 py-2 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-primary transition-all text-sm"
            value={selectedSku}
            onChange={(e) => setSelectedSku(e.target.value)}
          />
        </div>
        <div className="flex items-center space-x-2 bg-gray-50 px-3 py-2 rounded-xl border border-transparent">
          <Calendar className="w-4 h-4 text-gray-400" />
          <select 
            className="bg-transparent border-none text-sm font-medium text-gray-700 focus:ring-0 cursor-pointer"
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
          >
            <option value={7}>7 días</option>
            <option value={14}>14 días</option>
            <option value={30}>30 días</option>
          </select>
        </div>
        <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-400">
          <Filter className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-[450px]">
          <ForecastLineChart data={mockData} title="Pronóstico de Ventas Semanal" />
        </div>
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-slate-950 to-blue-900 p-6 rounded-2xl text-white shadow-xl relative overflow-hidden">
            <TrendingUp className="absolute -right-4 -bottom-4 w-32 h-32 text-white/5 rotate-12" />
            <p className="text-blue-200 text-xs font-bold uppercase tracking-widest mb-2">Mejor Modelo</p>
            <h4 className="text-3xl font-bold mb-1">Prophet</h4>
            <p className="text-blue-100 text-sm opacity-80">Error promedio: 8.32%</p>
            <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-between">
              <span className="text-xs text-blue-200">Confianza: 95%</span>
              <span className="px-2 py-1 bg-green-500/20 text-green-300 text-[10px] font-bold rounded uppercase">Óptimo</span>
            </div>
          </div>
          <ModelComparisonTable models={mockModels} />
        </div>
      </div>
    </div>
  );
};

export default Forecast;
