import { AlertTriangle, ChevronRight } from "lucide-react";
import BrandLoader from "../../../shared/ui/BrandLoader";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import api from "../../../shared/api/axios.instance";
import { useActiveBusinessId, useActiveStoreNbr } from "../../auth/store/authStore";

// ─── Tipos ────────────────────────────────────────────────────────────────────

interface AlertItem {
  family: string; // el producto/SKU
  current_stock: number;
  reorder_point_s: number;
  order_quantity: number | null;
  needs_cost_setup: boolean;
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
  const businessId = useActiveBusinessId();
  const storeNbr = useActiveStoreNbr();

  const { data, isLoading } = useQuery<AlertsResponse>({
    queryKey: ["inventory", "alerts", businessId, storeNbr, 5],
    queryFn: async () => {
      const { data } = await api.get(`/inventory/alerts?business_id=${businessId}&store_nbr=${storeNbr}&limit=5&sort_by=urgency`);
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
          <span className="text-sm font-semibold text-gray-700">Productos bajo el punto de reorden</span>
          {data && data.count > 0 && (
            <span className="text-xs font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded-full">{data.count}</span>
          )}
        </div>
        <button
          onClick={() => navigate("/inventory")}
          className="text-xs text-orange-600 hover:opacity-80 font-medium"
        >
          {data && data.count > alerts.length ? `Ver las ${data.count}` : "Ver todas"}
        </button>
      </div>

      {isLoading && (
        <BrandLoader label="Revisando tu stock..." size={32} className="py-6" />
      )}

      {!isLoading && alerts.length === 0 && (
        <div className="text-xs text-gray-400 py-4 text-center">
          Todo en orden: ningún producto está bajo su punto de reorden.
        </div>
      )}

      <ul className="divide-y divide-gray-50">
        {alerts.map((item) => (
          <li key={item.family}>
            <button
              onClick={() => navigate(`/inventory?producto=${encodeURIComponent(item.family)}`)}
              className="w-full flex items-center justify-between gap-2 py-2.5 text-left group"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate group-hover:text-orange-700">{item.family}</p>
                <p className="text-xs text-gray-400">
                  Stock {Math.round(item.current_stock).toLocaleString("es-CL")} · reordenar en {Math.round(item.reorder_point_s).toLocaleString("es-CL")}
                  {item.needs_cost_setup && <span className="text-red-500"> · falta costo</span>}
                </p>
              </div>
              <span className="flex items-center gap-1 shrink-0">
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${urgencyStyle[item.urgency] ?? urgencyStyle.normal}`}>
                  {urgencyLabel[item.urgency] ?? item.urgency}
                </span>
                <ChevronRight className="w-3.5 h-3.5 text-gray-300 group-hover:text-orange-600" />
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
