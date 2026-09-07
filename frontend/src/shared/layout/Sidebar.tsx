import { NavLink, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  TrendingUp,
  ShoppingBag,
  Sparkles,
  Database,
  LogOut,
  Package,
  ClipboardList,
  X,
  Shield,
} from "lucide-react";
import { useAuthStore } from "../../features/auth/store/authStore";
import { cn } from "../lib/utils";
import logoSymbol from "../../assets/svg/smartsupply-symbol.svg";

const navItems = [
  { name: "Inicio",            path: "/dashboard",   icon: LayoutDashboard },
  { name: "Subir ventas",      path: "/ingest",      icon: Sparkles },
  { name: "Datos",             path: "/datos",       icon: Database },
  { name: "Predecir demanda",  path: "/forecasting", icon: TrendingUp },
  { name: "Inventario",        path: "/inventory",   icon: Package },
  { name: "Ordenes",           path: "/orders",      icon: ClipboardList },
  { name: "Mis productos",     path: "/products",    icon: ShoppingBag },
];

interface SidebarProps {
  open?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ open = false, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore((s) => ({ user: s.user, logout: s.logout }));
  const queryClient = useQueryClient();

  return (
    <>
      {/* Backdrop mobile: cierra el drawer al tocar afuera */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "w-64 bg-slate-950 text-white flex flex-col flex-shrink-0 h-screen",
          "fixed inset-y-0 left-0 z-50 transition-transform duration-200 ease-out",
          "md:static md:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="px-5 py-5 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 bg-white/10 border border-white/20">
            <img src={logoSymbol} alt="" className="w-5 h-5" />
          </div>
          <span className="text-lg font-bold tracking-tight flex-1">SmartSupply</span>
          <button
            onClick={onClose}
            aria-label="Cerrar menu"
            className="md:hidden w-9 h-9 flex items-center justify-center text-white/60 hover:text-white rounded-lg hover:bg-white/10"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mx-5 border-t border-white/10" />

        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {(user?.role === "platform_admin"
            ? [...navItems, { name: "Admin", path: "/admin", icon: Shield }]
            : navItems
          ).map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className="group relative flex items-center gap-3 py-2.5 pl-[9px] rounded-lg text-sm font-medium"
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.span
                      layoutId="sidebar-active-pill"
                      className="absolute inset-0 rounded-lg bg-white/10 border-l-[3px] border-l-orange-600"
                      transition={{ type: "spring", stiffness: 550, damping: 38 }}
                    />
                  )}
                  <item.icon
                    className={cn(
                      "relative z-10 w-4 h-4 flex-shrink-0 transition-colors",
                      isActive ? "text-white" : "text-white/50 group-hover:text-white"
                    )}
                  />
                  <span
                    className={cn(
                      "relative z-10 transition-colors",
                      isActive ? "text-white" : "text-white/50 group-hover:text-white"
                    )}
                  >
                    {item.name}
                  </span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 space-y-1">
          <div className="rounded-xl px-4 py-3 mb-2 border border-white/10 bg-white/5">
            <p className="text-xs text-orange-400 font-semibold truncate mb-0.5">{user?.business_name ?? ""}</p>
            <p className="text-sm font-semibold text-white truncate">{user?.name ?? "Usuario"}</p>
            <p className="text-xs text-white/40 mt-0.5 capitalize">
            {user?.role === "platform_admin" ? "Admin plataforma" : user?.role === "business_admin" ? "Administrador" : "Analista"}
          </p>
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
    </>
  );
}
