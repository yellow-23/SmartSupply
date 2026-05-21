import { Target, AlertTriangle, ClipboardList, Activity, RefreshCw, Upload, FileDown, Loader2, Sparkles } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { KpiCard } from "../components/ui/KpiCard";
import AlertsSummaryPanel from "../components/ui/AlertsSummaryPanel";
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
import api from "../api/axios.instance";
import { useAuthStore } from "../store/authStore";

interface DashboardKPIs {
  mape_global: number | null;
  skus_en_alerta: number;
  ordenes_pendientes: number;
  nivel_servicio: number | null;
}

interface ChartPoint {
  date: string;
  real: number | null;
  forecast: number | null;
}

async function fetchKPIs(): Promise<DashboardKPIs> {
  const { data } = await api.get("/dashboard/kpis");
  return data;
}

async function fetchChartData(): Promise<ChartPoint[]> {
  const { data } = await api.get("/dashboard/chart-data");
  return data;
}

const quickActions = [
  { label: "Predecir demanda", icon: RefreshCw, href: "/forecasting" },
  { label: "Subir más ventas",  icon: Upload,   href: "/ingest" },
  { label: "Exportar reporte",  icon: FileDown, href: "#" },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const user = useAuthStore(s => s.user);

  const {
    data: kpis,
    isLoading: kpisLoading,
    isError: kpisError,
  } = useQuery<DashboardKPIs>({
    queryKey: ["dashboard", "kpis"],
    queryFn: fetchKPIs,
    staleTime: 300_000,
    refetchInterval: 300_000,
  });

  const {
    data: chartData = [],
    isLoading: chartLoading,
    isSuccess: chartLoaded,
  } = useQuery<ChartPoint[]>({
    queryKey: ["dashboard", "chart-data"],
    queryFn: fetchChartData,
    staleTime: 300_000,
    refetchInterval: 300_000,
  });

  const isEmptyState = chartLoaded && chartData.length === 0;

  const fmt = (v: number | null | undefined, suffix = "") =>
    v == null ? "—" : `${v.toLocaleString("es-CL")}${suffix}`;

  // ─── Onboarding: usuario sin ventas cargadas ──────────────────────────────
  if (isEmptyState) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-12 max-w-xl text-center space-y-6">
          <div className="w-20 h-20 bg-orange-50 rounded-2xl flex items-center justify-center mx-auto">
            <Sparkles className="w-10 h-10 text-orange-600" />
          </div>
          <div className="space-y-2">
            <h2 className="text-3xl font-bold text-gray-800">
              Hola {user?.name?.split(" ")[0] ?? "bienvenido"} 👋
            </h2>
            <p className="text-gray-500 text-base">
              Para empezar, sube tu primer archivo de ventas. Stocky se encarga de leer fotos, Excel o PDFs y dejar todo ordenado.
            </p>
          </div>
          <button
            onClick={() => navigate("/ingest")}
            className="px-7 py-3 bg-orange-600 text-white rounded-xl font-bold text-base hover:opacity-90 transition-all inline-flex items-center gap-2"
          >
            <Upload className="w-5 h-5" />
            Subir mis ventas
          </button>
          <p className="text-xs text-gray-400">
            Una vez que cargues tus datos podrás ver tu dashboard y predecir tu demanda.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {kpisError && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          No se pudo cargar los KPIs. Verifica que el backend esté activo.
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard
          label="MAPE global"
          value={kpisLoading ? "…" : fmt(kpis?.mape_global, "%")}
          icon={<Target className="w-full h-full" />}
        />
        <KpiCard
          label="SKUs en alerta"
          value={kpisLoading ? "…" : fmt(kpis?.skus_en_alerta)}
          icon={<AlertTriangle className="w-full h-full" />}
          valueClassName={kpis && kpis.skus_en_alerta > 0 ? "text-danger" : undefined}
        />
        <KpiCard
          label="Órdenes pendientes"
          value={kpisLoading ? "…" : fmt(kpis?.ordenes_pendientes)}
          icon={<ClipboardList className="w-full h-full" />}
        />
        <KpiCard
          label="Nivel de servicio"
          value={kpisLoading ? "…" : fmt(kpis?.nivel_servicio, "%")}
          icon={<Activity className="w-full h-full" />}
        />
      </div>

      {/* Chart + Panel lateral */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-semibold text-gray-700">Ventas vs predicción · 28 días</span>
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

          {chartLoading ? (
            <div className="flex items-center justify-center h-60 text-gray-400">
              <Loader2 className="w-6 h-6 animate-spin mr-2" />
              <span className="text-sm">Cargando datos…</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <ComposedChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
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
          )}
        </div>
        <div className="flex flex-col gap-4">
          <AlertsSummaryPanel />
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-accent">⚡</span>
              <span className="text-sm font-semibold text-gray-700">Acciones rápidas</span>
            </div>
            <div className="space-y-1">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => navigate(action.href)}
                  className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-blue-900 flex items-center justify-center text-white">
                      <action.icon className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900">
                      {action.label}
                    </span>
                  </div>
                  <span className="text-gray-300 group-hover:text-gray-400 text-xl leading-none">›</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
