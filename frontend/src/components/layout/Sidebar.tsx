import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { 
  LayoutDashboard, 
  TrendingUp, 
  Package, 
  ClipboardList, 
  Bot, 
  LogOut,
  Settings
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";

const Sidebar = () => {
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  const menuItems = [
    { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { name: "Forecasting", path: "/forecast", icon: TrendingUp },
    { name: "Inventario", path: "/inventory", icon: Package },
    { name: "Órdenes", path: "/orders", icon: ClipboardList },
    { name: "Ingesta IA", path: "/ingest", icon: Bot },
  ];

  return (
    <aside className="w-64 bg-[#1A1A2E] text-white flex flex-col shadow-xl flex-shrink-0">
      <div className="p-6 flex items-center space-x-3 border-b border-white/5">
        <div className="w-8 h-8 bg-[#2E75B6] rounded-lg flex items-center justify-center font-bold text-white text-xl">
          S
        </div>
        <span className="text-xl font-bold tracking-tight">SmartSupply</span>
      </div>
      
      <nav className="flex-1 p-4 space-y-1 mt-4">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              "flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 group " +
              (isActive ? "bg-[#2E75B6] text-white" : "text-gray-400 hover:bg-white/5 hover:text-white")
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-white/5">
        <button 
          onClick={handleLogout}
          className="w-full flex items-center space-x-3 px-4 py-3 text-red-400 hover:bg-red-500/10 rounded-xl transition-all"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Cerrar Sesión</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
