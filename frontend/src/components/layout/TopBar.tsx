import { Bell, Search } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

const pageMeta: Record<string, { title: string; subtitle: string }> = {
  "/dashboard":   { title: "Dashboard",         subtitle: `Resumen de operación · ${new Date().toLocaleDateString("es-CL", { day: "numeric", month: "short", year: "numeric" })}` },
  "/forecasting": { title: "Predicción de ventas", subtitle: "El sistema elige automáticamente el mejor modelo para cada producto" },
  "/inventory":   { title: "Inventario",          subtitle: "Cuándo y cuánto pedir para mantener el stock óptimo" },
  "/orders":      { title: "Órdenes de compra",   subtitle: "Generadas automáticamente según tus niveles de stock" },
  "/products":    { title: "Productos",           subtitle: "Catálogo maestro" },
  "/ingest":      { title: "Importar datos",      subtitle: "Sube fotos, Excel o PDF — la IA extrae los datos por ti" },
};

export default function TopBar() {
  const { pathname } = useLocation();
  const user = useAuthStore((s) => s.user);
  const meta = pageMeta[pathname] ?? { title: "SmartSupply", subtitle: "" };
  const initials = user?.name?.split(" ").map((n) => n[0]).slice(0, 2).join("") ?? "CF";

  return (
    <header className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-6 flex-shrink-0">
      <div>
        <h1 className="text-lg font-bold text-gray-900 leading-tight">{meta.title}</h1>
        <p className="text-xs text-gray-400">{meta.subtitle}</p>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar producto..."
            className="pl-9 pr-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg w-52 focus:outline-none focus:ring-2 focus:ring-nav-active/30 focus:border-nav-active transition-colors"
          />
        </div>
        <button aria-label="Notificaciones" className="w-9 h-9 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
          <Bell className="w-5 h-5" />
        </button>
        <div
          className="w-9 h-9 rounded-full bg-blue-900 flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
        >
          {initials}
        </div>
      </div>
    </header>
  );
}
