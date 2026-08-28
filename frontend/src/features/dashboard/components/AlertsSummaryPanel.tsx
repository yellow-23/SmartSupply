import { AlertTriangle, ChevronRight } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import api from "../../../shared/api/axios.instance";
import { useAuthStore } from "../../auth/store/authStore";

// ─── Tipos ────────────────────────────────────────────────────────────────────

interface AlertItem {
  sku_id: string;
  current_stock: number;
  reorder_point_s: number;
  order_quantity: number;
  policy: string;
  urgency: "critical" | "high" | "normal";
}

interface AlertsResponse {
  store_nbr: number;
  alerts: AlertItem[];
  count: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const urgencyLabel: Record<string, string> = {
  critical: "Crítico",
  high:     "Alto",
  normal:   "Normal",
};

const urgencyStyle: Record<string, string> = {
  critical: "text-red-600 bg-red-50",
  high:     "text-amber-600 bg-amber-50",
  normal:   "text-blue-600 bg-blue-50",
};

// ─── Componente ───────────────────────────────────────────────────────────────

export default function AlertsSummaryPanel() {
  const navigate = useNavigate();
  const user = useAuthStore(s => s.user);
  const businessId = user?.business_id;

  const { data, isLoading } = useQuery<AlertsResponse>({
    queryKey: ["inventory", "alerts", businessId, 5],
    queryFn: async () => {
      const { data } = await api.get(`/inventory/alerts?business_id=${businessId}&limit=5&sort_by=urgency`);
      return data;
    },
    enabled: !!businessId,
    staleTime: 300_000,
    refetchInterval: 300_000,
  });

  const alerts = data?.alerts ?? [];

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <span className="text-sm font-semibold text-gray-700">SKUs en alerta</span>
        </div>
        <button
          onClick={() => navigate("/inventory")}
          className="text-xs text-orange-600 hover:opacity-80 font-medium"
        >
          Ver todas
        </button>
      </div>

      {isLoading && (
        <div className="text-xs text-gray-400 py-4 text-center">Cargando…</div>
      )}

      {!isLoading && alerts.length === 0 && (
        <div className="text-xs text-gray-400 py-4 text-center">
          Sin alertas activas.
        </div>
      )}

      <ul className="space-y-2">
        {alerts.map((item) => (
          <li key={item.sku_id} className="flex items-center justify-between gap-2 text-sm">
            <div className="flex items-center gap-2 min-w-0">
              <span className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full ${urgencyStyle[item.urgency] ?? urgencyStyle.normal}`}>
                {urgencyLabel[item.urgency] ?? item.urgency}
              </span>
              <span className="truncate text-gray-700 font-mono text-xs">{item.sku_id}</span>
            </div>
            <button
              onClick={() => navigate("/inventory")}
              className="shrink-0 text-xs text-gray-500 hover:text-orange-600 flex items-center gap-0.5 transition-colors"
            >
              Ver alerta
              <ChevronRight className="w-3 h-3" />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
