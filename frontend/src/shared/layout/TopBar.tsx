import { useEffect } from "react";
import { Building2, MapPin, Menu } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore, useActiveBusinessId, useActiveStoreNbr } from "../../features/auth/store/authStore";
import { listBusinesses, listBusinessStores, storeLabel } from "../api/data";

const pageMeta: Record<string, { title: string; subtitle: string }> = {
  "/dashboard":   { title: "Dashboard",         subtitle: `Resumen de operación · ${new Date().toLocaleDateString("es-CL", { day: "numeric", month: "short", year: "numeric" })}` },
  "/forecasting": { title: "Predicción de ventas", subtitle: "El sistema elige automáticamente el mejor modelo para cada producto" },
  "/inventory":   { title: "Inventario",          subtitle: "Cuándo y cuánto pedir para mantener el stock óptimo" },
  "/orders":      { title: "Órdenes de compra",   subtitle: "Crea, envía y recibe pedidos a tus proveedores" },
  "/products":    { title: "Productos",           subtitle: "Catálogo: familia, proveedor, costos y tiempos de entrega" },
  "/ingest":      { title: "Importar datos",      subtitle: "Sube fotos, Excel o PDF — la IA extrae los datos por ti" },
  "/datos":       { title: "Datos",               subtitle: "Historial de cargas: revisa, edita, revierte o elimina" },
  "/negocio":     { title: "Mi negocio",          subtitle: "Datos de la empresa, ubicaciones y tus otros negocios" },
};

const selectCls =
  "max-w-[9rem] sm:max-w-[14rem] truncate pl-8 pr-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-nav-active/30 focus:border-nav-active";

interface TopBarProps {
  onMenuClick?: () => void;
}

export default function TopBar({ onMenuClick }: TopBarProps) {
  const { pathname } = useLocation();
  const user = useAuthStore((s) => s.user);
  const meta = pageMeta[pathname] ?? { title: "SmartSupply", subtitle: "" };
  const activeBusinessId = useActiveBusinessId();
  const activeStoreNbr = useActiveStoreNbr();
  const setActiveBusiness = useAuthStore((s) => s.setActiveBusiness);
  const setActiveStore = useAuthStore((s) => s.setActiveStore);
  const { data: businesses = [] } = useQuery({
    queryKey: ["businesses", user?.id],
    queryFn: listBusinesses,
    enabled: !!user,
  });
  const { data: stores = [] } = useQuery({
    queryKey: ["stores", activeBusinessId],
    queryFn: () => listBusinessStores(activeBusinessId!),
    enabled: activeBusinessId != null,
  });

  // Negocio guardado que ya no es accesible (lo quitaron del usuario): volver al principal.
  useEffect(() => {
    if (businesses.length && activeBusinessId && !businesses.some((b) => b.id === activeBusinessId)) {
      setActiveBusiness(user?.business_id ?? businesses[0].id);
    }
  }, [businesses, activeBusinessId]);

  // Ubicacion guardada que no existe en este negocio: usar la primera.
  useEffect(() => {
    if (stores.length && !stores.some((s) => s.store_nbr === activeStoreNbr)) {
      setActiveStore(stores[0].store_nbr);
    }
  }, [stores, activeStoreNbr]);

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
      <div className="flex items-center gap-2 flex-shrink-0">
        {businesses.length > 0 && (
          <div className="relative">
            <Building2 className="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <select
              aria-label="Negocio activo"
              value={activeBusinessId ?? ""}
              onChange={(e) => setActiveBusiness(Number(e.target.value))}
              className={selectCls}
            >
              {businesses.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>
        )}
        {stores.length > 1 && (
          <div className="relative hidden sm:block">
            <MapPin className="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <select
              aria-label="Ubicación activa"
              value={activeStoreNbr}
              onChange={(e) => setActiveStore(Number(e.target.value))}
              className={selectCls}
            >
              {stores.map((s) => (
                <option key={s.store_nbr} value={s.store_nbr}>{storeLabel(s)}</option>
              ))}
            </select>
          </div>
        )}
        <Link
          to="/negocio"
          title="Mi negocio"
          className="w-9 h-9 rounded-full bg-blue-900 flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
        >
          {initials}
        </Link>
      </div>
    </header>
  );
}
