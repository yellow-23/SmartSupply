import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  TrendingUp,
  Package,
  ClipboardList,
  ShoppingBag,
  Sparkles,
  LogOut,
  BarChart3,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import { cn } from "../../lib/utils";

const navSections = [
  {
    label: "OPERACIÓN",
    items: [
      { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
      { name: "Predicción de ventas", path: "/forecasting", icon: TrendingUp },
      { name: "Inventario", path: "/inventory", icon: Package },
      { name: "Órdenes", path: "/orders", icon: ClipboardList },
    ],
  },
  {
    label: "CATÁLOGO",
    items: [
      { name: "Productos", path: "/products", icon: ShoppingBag },
      { name: "Importar datos", path: "/ingest", icon: Sparkles },
    ],
  },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore((s) => ({ user: s.user, logout: s.logout }));

  return (
    <aside className="w-64 bg-slate-950 text-white flex flex-col flex-shrink-0 h-screen">
      <div className="px-5 py-5 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 bg-white/10 border border-white/20">
          <BarChart3 className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-bold tracking-tight">SmartSupply</span>
      </div>

      <div className="mx-5 border-t border-white/10" />

      <nav className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {navSections.map((section) => (
          <div key={section.label}>
            <p className="px-3 mb-2 text-[10px] font-semibold text-white/40 uppercase tracking-widest">
              {section.label}
            </p>
            <div className="space-y-0.5">
              {section.items.map((item) => (
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
            </div>
          </div>
        ))}
      </nav>

      <div className="p-3 space-y-1">
        <div className="rounded-xl px-4 py-3 mb-2 border border-white/10 bg-white/5">
          <p className="text-sm font-semibold text-white truncate">{user?.name ?? "Usuario"}</p>
          <p className="text-xs text-white/40 mt-0.5 capitalize">{user?.role === "admin" ? "Administrador" : "Analista"}</p>
        </div>
        <button
          onClick={() => { logout(); navigate("/login"); }}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-red-400 hover:bg-red-500/10 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
