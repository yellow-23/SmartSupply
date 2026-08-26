import { Bell, Menu, Search } from "lucide-react";
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

interface TopBarProps {
  onMenuClick?: () => void;
}

export default function TopBar({ onMenuClick }: TopBarProps) {
  const { pathname } = useLocation();
  const user = useAuthStore((s) => s.user);
  const meta = pageMeta[pathname] ?? { title: "SmartSupply", subtitle: "" };
  const initials = user?.name?.split(" ").map((n) => n[0]).slice(0, 2).join("") ?? "CF";

  return (
    <header className="h-16 bg-white border-b border-gray-100 flex items-center justify-between gap-3 px-4 md:px-6 flex-shrink-0">
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onMenuClick}
          aria-label="Abrir menu"
          className="md:hidden w-9 h-9 flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="min-w-0">
          <h1 className="text-base md:text-lg font-bold text-gray-900 leading-tight truncate">{meta.title}</h1>
          <p className="text-xs text-gray-400 truncate hidden sm:block">{meta.subtitle}</p>
        </div>
      </div>
      <div className="flex items-center gap-2 md:gap-3 flex-shrink-0">
        <div className="relative hidden lg:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar producto..."
            className="pl-9 pr-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg w-52 focus:outline-none focus:ring-2 focus:ring-nav-active/30 focus:border-nav-active transition-colors"
          />
        </div>
        <button aria-label="Notificaciones" className="w-9 h-9 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0">
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
