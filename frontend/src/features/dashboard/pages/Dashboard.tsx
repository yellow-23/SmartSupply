import { Target, AlertTriangle, ClipboardList, Activity, RefreshCw, Upload, FileDown, Zap, Sparkles } from "lucide-react";
import BrandLoader from "../../../shared/ui/BrandLoader";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { listBusinesses } from "../../../shared/api/data";
import { KpiCard } from "../components/KpiCard";
import AlertsSummaryPanel from "../components/AlertsSummaryPanel";
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
import api from "../../../shared/api/axios.instance";
import { useAuthStore, useActiveBusinessId, useActiveStoreNbr } from "../../auth/store/authStore";
import { exportAlerts } from "../../inventory/api/inventory";
import { downloadBlob } from "../../../shared/lib/utils";

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

async function fetchKPIs(businessId: number | null): Promise<DashboardKPIs> {
  const { data } = await api.get("/dashboard/kpis", { params: { business_id: businessId } });
  return data;
}

interface ChartData {
  points: ChartPoint[];
  forecast_skus: string[];
  total_skus: number;
}

async function fetchChartData(businessId: number | null): Promise<ChartData> {
  const { data } = await api.get("/dashboard/chart-data", { params: { business_id: businessId } });
  return data;
}

interface StoreForecast {
  store_nbr: number;
  unit: "CLP" | "units";
  model_used: string;
  wape: number | null;
  horizon_days: number;
  points: ChartPoint[];
}

async function fetchStoreForecast(businessId: number | null, storeNbr: number, horizon: number): Promise<StoreForecast> {
  const { data } = await api.get("/dashboard/store-forecast", {
    params: { business_id: businessId, store_nbr: storeNbr, horizon_days: horizon },
  });
  return data;
}

const MODEL_NAMES: Record<string, string> = { arima: "ARIMA", prophet: "Prophet", xgboost: "XGBoost", lstm: "LSTM" };
const fmtCompactCLP = (v: number) =>
  v >= 1_000_000 ? `$${(v / 1_000_000).toLocaleString("es-CL", { maximumFractionDigits: 1 })}M`
  : v >= 1_000 ? `$${Math.round(v / 1_000).toLocaleString("es-CL")}k` : `$${Math.round(v)}`;
const fmtShortDate = (d: string) =>
  new Date(`${d}T12:00:00`).toLocaleDateString("es-CL", { day: "numeric", month: "short" });

const quickActions = [
  { label: "Predecir demanda", icon: RefreshCw, href: "/forecasting" },
  { label: "Subir más ventas",  icon: Upload,   href: "/ingest" },
  { label: "Exportar alertas (Excel)", icon: FileDown, href: null },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const user = useAuthStore(s => s.user);
  const businessId = useActiveBusinessId();
  const storeNbr = useActiveStoreNbr();
  const [horizon, setHorizon] = useState<14 | 30>(14);
  const { data: businesses = [] } = useQuery({ queryKey: ["businesses", user?.id], queryFn: listBusinesses, enabled: !!user });
  const business = businesses.find(b => b.id === businessId);
  const businessIncomplete = business?.my_role === "owner" && (!business.rut || !business.city || !business.address);

  const {
    data: kpis,
    isLoading: kpisLoading,
    isError: kpisError,
  } = useQuery<DashboardKPIs>({
    queryKey: ["dashboard", "kpis", user?.id, businessId],
    queryFn: () => fetchKPIs(businessId),
    staleTime: 300_000,
    refetchInterval: 300_000,
    enabled: !!user,
  });

  // Solo para saber si el negocio ya tiene ventas (onboarding vs tablero)
  const {
    data: chart,
    isLoading: chartLoading,
    isSuccess: chartLoaded,
  } = useQuery<ChartData>({
    queryKey: ["dashboard", "chart-data", user?.id, businessId],
    queryFn: () => fetchChartData(businessId),
    staleTime: 300_000,
    enabled: !!user,
  });
  const isEmptyState = chartLoaded && (chart?.points.length ?? 0) === 0;

  // Proyeccion de la venta total de la ubicacion activa (AMS sobre la suma de todos los productos)
  const storeForecast = useQuery<StoreForecast>({
    queryKey: ["dashboard", "store-forecast", businessId, storeNbr, horizon],
    queryFn: () => fetchStoreForecast(businessId, storeNbr, horizon),
    enabled: !!user && chartLoaded && !isEmptyState,
    staleTime: 600_000,
    retry: false,
  });
  const sf = storeForecast.data;
  const isCLP = sf?.unit === "CLP";
  const fmtValue = (v: number) => (isCLP ? fmtCompactCLP(v) : Math.round(v).toLocaleString("es-CL"));
  const forecastError = (storeForecast.error as any)?.response?.data?.detail;

  const fmt = (v: number | null | undefined, suffix = "") =>
    v == null ? "—" : `${v.toLocaleString("es-CL")}${suffix}`;

  // Hasta saber si el negocio tiene ventas no se muestra ni el tablero ni el onboarding
  if (chartLoading) {
    return <BrandLoader label="Cargando tu negocio..." className="min-h-[60vh]" />;
  }

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
            className="px-7 py-3 bg-orange-600 text-white rounded-xl font-bold text-base hover:opacity-90 transition-all active:scale-[0.97] inline-flex items-center gap-2"
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
      {businessIncomplete && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800 flex flex-wrap items-center justify-between gap-2">
          <span>A {business!.name} le faltan datos (RUT, ciudad o dirección) que van en tus órdenes de compra.</span>
          <Link to="/negocio" className="font-semibold underline">Completar ahora</Link>
        </div>
      )}
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
          delay={0}
        />
        <KpiCard
          label="SKUs en alerta"
          value={kpisLoading ? "…" : fmt(kpis?.skus_en_alerta)}
          icon={<AlertTriangle className="w-full h-full" />}
          valueClassName={kpis && kpis.skus_en_alerta > 0 ? "text-danger" : undefined}
          delay={0.03}
        />
        <KpiCard
          label="Órdenes pendientes"
          value={kpisLoading ? "…" : fmt(kpis?.ordenes_pendientes)}
          icon={<ClipboardList className="w-full h-full" />}
          delay={0.06}
        />
        <KpiCard
          label="Nivel de servicio"
          value={kpisLoading ? "…" : fmt(kpis?.nivel_servicio, "%")}
          icon={<Activity className="w-full h-full" />}
          delay={0.09}
        />
      </div>

      {/* Chart + Panel lateral */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
            <div>
              <span className="text-sm font-semibold text-gray-700">
                Venta total de la tienda {isCLP ? "(CLP)" : sf ? "(unidades)" : ""}
              </span>
              <p className="text-xs text-gray-400">
                {sf
                  ? `Últimas 4 semanas y proyección a ${sf.horizon_days} días · ${MODEL_NAMES[sf.model_used] ?? sf.model_used}${sf.wape != null ? ` · ${sf.wape.toFixed(1)}% de error` : ""}`
                  : "Todos los productos de la ubicación activa"}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-3 text-xs text-gray-500">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary inline-block" />
                  Real
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-accent inline-block" />
                  Proyectado
                </span>
              </div>
              <div className="flex rounded-lg border border-gray-200 overflow-hidden text-xs" role="group" aria-label="Días a proyectar">
                {([14, 30] as const).map(h => (
                  <button
                    key={h}
                    onClick={() => setHorizon(h)}
                    aria-pressed={horizon === h}
                    className={`px-2.5 py-1.5 ${horizon === h ? "bg-orange-600 text-white" : "text-gray-600 hover:bg-gray-50"}`}
                  >
                    {h} días
                  </button>
                ))}
              </div>
            </div>
          </div>

          {storeForecast.isLoading ? (
            <BrandLoader
              label="Proyectando la venta de tu tienda..."
              hint="El sistema prueba varios modelos y elige el más preciso. La primera vez tarda unos segundos."
              className="h-60"
            />
          ) : forecastError ? (
            <div className="h-60 flex items-center justify-center text-center text-sm text-gray-400 px-6">
              {forecastError.message ?? "No se pudo calcular la proyección de la tienda."}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <ComposedChart data={sf?.points ?? []} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="gradReal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1565C0" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#1565C0" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
                <XAxis dataKey="date" tickFormatter={fmtShortDate} tick={{ fontSize: 11, fill: "#9CA3AF" }} tickLine={false} axisLine={false} minTickGap={24} />
                <YAxis tickFormatter={fmtValue} tick={{ fontSize: 11, fill: "#9CA3AF" }} tickLine={false} axisLine={false} width={56} />
                <Tooltip
                  contentStyle={{ border: "1px solid #E5E7EB", borderRadius: 8, fontSize: 12 }}
                  labelFormatter={(d) => fmtShortDate(String(d))}
                  formatter={(v: number) => (isCLP ? `$${Math.round(v).toLocaleString("es-CL")}` : `${Math.round(v).toLocaleString("es-CL")} uds`)}
                />
                <Area type="monotone" dataKey="real" stroke="#1565C0" strokeWidth={2} fill="url(#gradReal)" dot={false} name="Real" />
                <Line type="monotone" dataKey="forecast" stroke="#E65100" strokeWidth={2} strokeDasharray="4 3" dot={false} name="Proyectado" />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </div>
        <div className="flex flex-col gap-4">
          <AlertsSummaryPanel />
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-accent" />
              <span className="text-sm font-semibold text-gray-700">Acciones rápidas</span>
            </div>
            <div className="space-y-1">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => action.href
                    ? navigate(action.href)
                    : businessId && exportAlerts(businessId).then(b => downloadBlob(b, `alertas_inventario_${businessId}.xlsx`))}
                  className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors active:scale-[0.98] group"
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
