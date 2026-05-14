import React from "react";
import { Target, AlertTriangle, FileCheck, DollarSign, ArrowUpRight } from "lucide-react";
import KPICard from "../components/KPICard";
import ForecastLineChart from "../components/ForecastLineChart";

const Dashboard = () => {
  const mockData = [
    { date: "Lun", actual: 4000, forecast: 4200 },
    { date: "Mar", actual: 3000, forecast: 3100 },
    { date: "Mie", actual: 2000, forecast: 2200 },
    { date: "Jue", actual: 2780, forecast: 2500 },
    { date: "Vie", actual: 1890, forecast: 2100 },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 tracking-tight">Panel de Control</h2>
        <p className="text-gray-500 mt-1">Resumen del rendimiento de la cadena de suministro</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard title="MAPE Global" value="8.3%" trend="-1.2%" icon={<Target />} color="text-green-600" />
        <KPICard title="Stock Crítico" value="12" subtext="SKUs bajo punto de reorden" icon={<AlertTriangle />} color="text-red-600" />
        <KPICard title="Órdenes" value="5" subtext="Pendientes de aprobación" icon={<FileCheck />} color="text-unab-light" />
        <KPICard title="Capital" value="$52.5M" trend="+3.5%" icon={<DollarSign />} color="text-blue-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-[400px]">
          <ForecastLineChart data={mockData} title="Evolución de Ventas vs Predicción" />
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-gray-800 mb-6">Acciones Rápidas</h3>
          <div className="space-y-3">
            <button className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 rounded-xl transition-all">
              <span className="font-medium text-gray-700 text-sm">Generar Órdenes</span>
              <ArrowUpRight className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
