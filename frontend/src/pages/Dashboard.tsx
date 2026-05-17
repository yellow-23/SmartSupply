import { Target, AlertTriangle, ClipboardList, DollarSign, RefreshCw, Upload, ShoppingCart, FileDown } from "lucide-react";
import { KpiCard } from "../components/ui/KpiCard";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

const salesData = [
  { date: "15 abr", real: 4200, forecast: 3900 },
  { date: "18 abr", real: 3800, forecast: 3700 },
  { date: "21 abr", real: 4600, forecast: 4400 },
  { date: "25 abr", real: 4100, forecast: 4200 },
  { date: "28 abr", real: 5200, forecast: 4900 },
  { date: "1 may",  real: 4800, forecast: 4700 },
  { date: "5 may",  real: 5500, forecast: 5200 },
  { date: "8 may",  real: 5100, forecast: 5000 },
  { date: "11 may", real: 5800, forecast: 5500 },
  { date: "14 may", real: 5400, forecast: 5300 },
];

const quickActions = [
  { label: "Reentrenar modelos", icon: RefreshCw,    href: "/forecasting" },
  { label: "Cargar ventas",      icon: Upload,       href: "/ingest" },
  { label: "Generar OC",         icon: ShoppingCart, href: "/orders" },
  { label: "Exportar reporte",   icon: FileDown,     href: "#" },
];

export default function Dashboard() {
  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard
          label="Precisión de predicción"
          value="8.4%"
          icon={<Target className="w-full h-full" />}
          trend={{ value: "-1.2 pts", direction: "down", isGood: true }}
        />
        <KpiCard
          label="Productos críticos"
          value="23"
          icon={<AlertTriangle className="w-full h-full" />}
          valueClassName="text-danger"
          trend={{ value: "+5 vs ayer", direction: "up", isGood: false }}
        />
        <KpiCard
          label="Órdenes Pend."
          value="47"
          icon={<ClipboardList className="w-full h-full" />}
          trend={{ value: "-8 vs ayer", direction: "down", isGood: true }}
        />
        <KpiCard
          label="Capital inmovilizado"
          value="$184M"
          icon={<DollarSign className="w-full h-full" />}
          trend={{ value: "+3.1%", direction: "up", isGood: false }}
        />
      </div>

      {/* Chart + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-semibold text-gray-700">Ventas vs predicción · 30 días</span>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-primary inline-block" />
                Real
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-accent inline-block" />
                Predicho
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <ComposedChart data={salesData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gradReal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1565C0" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#1565C0" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#9CA3AF" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#9CA3AF" }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ border: "1px solid #E5E7EB", borderRadius: 8, fontSize: 12 }} />
              <Area type="monotone" dataKey="real" stroke="#1565C0" strokeWidth={2} fill="url(#gradReal)" dot={false} name="Real" />
              <Line type="monotone" dataKey="forecast" stroke="#E65100" strokeWidth={2} strokeDasharray="4 3" dot={false} name="Predicho" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Quick actions */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-5">
            <span className="text-accent">⚡</span>
            <span className="text-sm font-semibold text-gray-700">Acciones rápidas</span>
          </div>
          <div className="space-y-1.5">
            {quickActions.map((action) => (
              <a
                key={action.label}
                href={action.href}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-lg bg-blue-900 flex items-center justify-center text-white"
                  >
                    <action.icon className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900">
                    {action.label}
                  </span>
                </div>
                <span className="text-gray-300 group-hover:text-gray-400 text-xl leading-none">›</span>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
