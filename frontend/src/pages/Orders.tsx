import { ShoppingCart, CheckCircle, Clock, Truck, Plus, Download } from "lucide-react";
import { StatusBadge } from "../components/ui/StatusBadge";

const orders = [
  { id: "OC-2024-0041", product: "Aceite Vegetal 1L", supplier: "Dist. Central", qty: 120, total: "$184.800", status: "Pendiente",  date: "14 may 2025" },
  { id: "OC-2024-0040", product: "Arroz Grano Largo 5kg", supplier: "Alimentos Sur", qty: 80, total: "$96.000", status: "Aprobada",  date: "13 may 2025" },
  { id: "OC-2024-0039", product: "Azúcar Blanca 1kg", supplier: "Dist. Central", qty: 200, total: "$120.000", status: "Aprobada",  date: "12 may 2025" },
  { id: "OC-2024-0038", product: "Detergente Líquido 3L", supplier: "Limpieza Pro", qty: 60, total: "$210.000", status: "Rechazada", date: "11 may 2025" },
  { id: "OC-2024-0037", product: "Leche Entera 1L", supplier: "Lácteos Norte", qty: 300, total: "$270.000", status: "Aprobada",  date: "10 may 2025" },
  { id: "OC-2024-0036", product: "Fideos Tallarín 500g", supplier: "Pastas Chile", qty: 150, total: "$75.000", status: "Pendiente",  date: "10 may 2025" },
];

const stats = [
  { label: "Pendientes",  value: "12", icon: Clock,        bg: "bg-amber-50",   text: "text-amber-500"  },
  { label: "Aprobadas",   value: "34", icon: CheckCircle,  bg: "bg-emerald-50", text: "text-emerald-500" },
  { label: "En tránsito", value: "8",  icon: Truck,        bg: "bg-blue-50",    text: "text-blue-900"   },
  { label: "Este mes",    value: "54", icon: ShoppingCart, bg: "bg-orange-50",  text: "text-orange-600" },
];

export default function Orders() {
  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {stats.map(({ label, value, icon: Icon, bg, text }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-4">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${bg}`}>
              <Icon className={`w-5 h-5 ${text}`} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              <p className="text-xs text-gray-400 font-medium">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50">
          <span className="text-sm font-semibold text-gray-700">Órdenes de compra</span>
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-2 px-3 py-2 text-sm text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <Download className="w-4 h-4" />
              Exportar
            </button>
            <button className="flex items-center gap-2 px-3 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 transition-colors">
              <Plus className="w-4 h-4" />
              Nueva orden
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["N° Orden", "Producto", "Proveedor", "Cantidad", "Total", "Estado", "Fecha"].map((h) => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs text-gray-500">{o.id}</td>
                  <td className="px-6 py-4 font-medium text-gray-800">{o.product}</td>
                  <td className="px-6 py-4 text-gray-500">{o.supplier}</td>
                  <td className="px-6 py-4 text-gray-700">{o.qty} un.</td>
                  <td className="px-6 py-4 font-semibold text-gray-800">{o.total}</td>
                  <td className="px-6 py-4"><StatusBadge status={o.status as any} /></td>
                  <td className="px-6 py-4 text-gray-400 text-xs">{o.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
