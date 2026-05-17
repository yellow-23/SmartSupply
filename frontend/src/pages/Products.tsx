import { Plus, Search, Package, TrendingUp, AlertTriangle, Download } from "lucide-react";
import { StatusBadge } from "../components/ui/StatusBadge";

const products = [
  { sku: "ACE-001", name: "Aceite Vegetal 1L",        category: "Abarrotes",  stock: 12,  minStock: 30,  price: "$1.540", status: "Alerta" },
  { sku: "ARR-005", name: "Arroz Grano Largo 5kg",    category: "Abarrotes",  stock: 85,  minStock: 40,  price: "$1.200", status: "Normal" },
  { sku: "AZU-001", name: "Azúcar Blanca 1kg",        category: "Abarrotes",  stock: 142, minStock: 50,  price: "$600",   status: "Normal" },
  { sku: "BEB-005", name: "Bebida Cola 1.5L",          category: "Bebidas",    stock: 5,   minStock: 15,  price: "$990",   status: "Alerta" },
  { sku: "DET-003", name: "Detergente Líquido 3L",    category: "Limpieza",   stock: 220, minStock: 30,  price: "$3.500", status: "Exceso" },
  { sku: "LEC-001", name: "Leche Entera 1L",           category: "Lácteos",    stock: 48,  minStock: 60,  price: "$900",   status: "Alerta" },
  { sku: "FID-002", name: "Fideos Tallarín 500g",     category: "Abarrotes",  stock: 96,  minStock: 40,  price: "$500",   status: "Normal" },
  { sku: "JAB-001", name: "Jabón en Barra x3",        category: "Limpieza",   stock: 310, minStock: 40,  price: "$1.200", status: "Exceso" },
];

const categories = ["Todos", "Abarrotes", "Bebidas", "Lácteos", "Limpieza"];

export default function Products() {
  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: "Total productos", value: "284", icon: Package,       bg: "bg-blue-50",    text: "text-blue-900"   },
          { label: "Con stock bajo",  value: "23",  icon: AlertTriangle, bg: "bg-red-50",     text: "text-red-500"    },
          { label: "Con exceso",      value: "11",  icon: TrendingUp,    bg: "bg-amber-50",   text: "text-amber-500"  },
          { label: "Categorías",      value: "8",   icon: Package,       bg: "bg-emerald-50", text: "text-emerald-500" },
        ].map(({ label, value, icon: Icon, bg, text }) => (
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
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-6 py-4 border-b border-gray-50">
          <div className="flex items-center gap-3">
            {categories.map((cat) => (
              <button
                key={cat}
                className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${cat === "Todos" ? "bg-blue-900 text-white" : "text-gray-500 hover:bg-gray-100"}`}
              >
                {cat}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar producto..."
                className="pl-9 pr-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg w-48 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
            <button className="flex items-center gap-2 px-3 py-2 text-sm text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <Download className="w-4 h-4" />
            </button>
            <button className="flex items-center gap-2 px-3 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 transition-colors">
              <Plus className="w-4 h-4" />
              Agregar
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["Código", "Producto", "Categoría", "Stock actual", "Stock mínimo", "Precio", "Estado"].map((h) => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {products.map((p) => (
                <tr key={p.sku} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs text-gray-400">{p.sku}</td>
                  <td className="px-6 py-4 font-medium text-gray-800">{p.name}</td>
                  <td className="px-6 py-4 text-gray-500">{p.category}</td>
                  <td className={`px-6 py-4 font-semibold ${p.stock < p.minStock ? "text-red-600" : "text-gray-800"}`}>{p.stock} un.</td>
                  <td className="px-6 py-4 text-gray-400">{p.minStock} un.</td>
                  <td className="px-6 py-4 text-gray-700">{p.price}</td>
                  <td className="px-6 py-4"><StatusBadge status={p.status as any} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
