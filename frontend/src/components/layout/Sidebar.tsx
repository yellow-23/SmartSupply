import { NavLink, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  LayoutDashboard,
  TrendingUp,
  ShoppingBag,
  Sparkles,
  Database,
  LogOut,
  BarChart3,
  Package,
  ClipboardList,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { cn } from "../../lib/utils";

const navItems = [
  { name: "Inicio",            path: "/dashboard",   icon: LayoutDashboard },
  { name: "Subir ventas",      path: "/ingest",      icon: Sparkles },
  { name: "Datos",             path: "/datos",       icon: Database },
  { name: "Predecir demanda",  path: "/forecasting", icon: TrendingUp },
  { name: "Inventario",        path: "/inventory",   icon: Package },
  { name: "Ordenes",           path: "/orders",      icon: ClipboardList },
  { name: "Mis productos",     path: "/products",    icon: ShoppingBag },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore((s) => ({ user: s.user, logout: s.logout }));
  const queryClient = useQueryClient();

  return (
    <aside className="w-64 bg-slate-950 text-white flex flex-col flex-shrink-0 h-screen">
      <div className="px-5 py-5 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 bg-white/10 border border-white/20">
          <BarChart3 className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-bold tracking-tight">SmartSupply</span>
      </div>

      <div className="mx-5 border-t border-white/10" />

      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 py-2.5 rounded-lg text-sm font-medium transition-colors border-l-[3px] pl-[9px]",
                isActive
                  ? "bg-white/10 text-white border-l-orange-600"
                  : "text-white/50 hover:bg-white/5 hover:text-white border-l-transparent"
              )
            }
          >
            <item.icon className="w-4 h-4 flex-shrink-0" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 space-y-1">
        <div className="rounded-xl px-4 py-3 mb-2 border border-white/10 bg-white/5">
          <p className="text-xs text-orange-400 font-semibold truncate mb-0.5">{user?.business_name ?? ""}</p>
          <p className="text-sm font-semibold text-white truncate">{user?.name ?? "Usuario"}</p>
          <p className="text-xs text-white/40 mt-0.5 capitalize">{user?.role === "admin" ? "Administrador" : "Analista"}</p>
        </div>
        <button
          onClick={() => { queryClient.clear(); logout(); navigate("/login"); }}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-red-400 hover:bg-red-500/10 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
