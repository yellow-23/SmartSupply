import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus, Search, Package, AlertTriangle, XCircle, Layers,
  ChevronLeft, ChevronRight, Pencil, Trash2,
} from "lucide-react";
import api from "../../api/axios.instance";
import type { ProductResponse, ProductPage } from "../../types/product";
import ProductFormModal from "../../components/forms/ProductFormModal";
import ConfirmModal from "../../components/ui/ConfirmModal";
import { PRODUCT_FAMILIES } from "../../constants/families";

// ─── Fetcher ──────────────────────────────────────────────────────────────────

async function fetchProducts(
  page: number,
  search: string,
  family: string,
  isActive: "all" | "active" | "inactive",
): Promise<ProductPage> {
  const params = new URLSearchParams({ page: String(page), limit: "20" });
  if (search) params.set("search", search);
  if (family) params.set("family", family);
  if (isActive !== "all") params.set("is_active", isActive === "active" ? "true" : "false");
  const { data } = await api.get(`/products?${params}`);
  return data;
}

// ─── Componente ───────────────────────────────────────────────────────────────

export default function ProductsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [family, setFamily] = useState("");
  const [isActive, setIsActive] = useState<"all" | "active" | "inactive">("active");
  const [showForm, setShowForm] = useState(false);
  const [editProduct, setEditProduct] = useState<ProductResponse | null>(null);
  const [deactivateTarget, setDeactivateTarget] = useState<ProductResponse | null>(null);
  const [deactivateBlocked, setDeactivateBlocked] = useState(false);

  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Debounce 300 ms
  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [searchInput]);

  const { data, isLoading, isError } = useQuery<ProductPage>({
    queryKey: ["products", page, search, family, isActive],
    queryFn: () => fetchProducts(page, search, family, isActive),
    staleTime: 60_000,
  });

  // Soft-delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/products/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] });
      setDeactivateTarget(null);
    },
  });

  // Verificar órdenes pendientes antes de mostrar confirm
  async function handleDeactivateClick(product: ProductResponse) {
    try {
      // orders.py filtra por status; el filtro por sku se añadirá en Sprint 4
      const { data: orders } = await api.get(`/orders?status=Pendiente`);
      const hasPending = Array.isArray(orders) && orders.some(
        (o: { sku_id?: string }) => o.sku_id === product.sku_id,
      );
      setDeactivateBlocked(hasPending);
    } catch {
      setDeactivateBlocked(false);
    }
    setDeactivateTarget(product);
  }

  const items = data?.items ?? [];

  return (
    <div className="space-y-6">

      {/* Summary cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <SummaryCard label="Total productos" value={data?.total ?? "—"}
          icon={<Package className="w-5 h-5 text-blue-600" />} bg="bg-blue-50" />
        <SummaryCard label="Activos" value={data?.total_active ?? "—"}
          icon={<Layers className="w-5 h-5 text-emerald-600" />} bg="bg-emerald-50" />
        <SummaryCard label="Inactivos" value={data?.total_inactive ?? "—"}
          icon={<XCircle className="w-5 h-5 text-gray-400" />} bg="bg-gray-50" />
        <SummaryCard label="Familias" value={data?.total_families ?? "—"}
          icon={<AlertTriangle className="w-5 h-5 text-amber-500" />} bg="bg-amber-50" />
      </div>

      {/* Table card */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-5 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2 flex-wrap">
            {(["all", "active", "inactive"] as const).map((v) => (
              <button
                key={v}
                onClick={() => { setIsActive(v); setPage(1); }}
                className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                  isActive === v ? "bg-blue-900 text-white" : "text-gray-500 hover:bg-gray-100"
                }`}
              >
                {v === "all" ? "Todos" : v === "active" ? "Activos" : "Inactivos"}
              </button>
            ))}
            <select
              value={family}
              onChange={(e) => { setFamily(e.target.value); setPage(1); }}
              className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="">Todas las familias</option>
              {PRODUCT_FAMILIES.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar SKU o nombre…"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-9 pr-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg w-52 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary"
              />
            </div>
            <button
              onClick={() => { setEditProduct(null); setShowForm(true); }}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Nuevo
            </button>
          </div>
        </div>

        {/* Error banner */}
        {isError && (
          <div className="px-5 py-3 text-sm text-red-600 bg-red-50">
            Error al cargar productos. Verifica que el backend esté activo.
          </div>
        )}

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {["SKU", "Nombre", "Familia", "Tienda", "Costo unit.", "Lead time", "MOQ", "Estado", ""].map((h) => (
                  <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {isLoading && (
                <tr><td colSpan={9} className="px-5 py-8 text-center text-sm text-gray-400">Cargando…</td></tr>
              )}
              {!isLoading && items.length === 0 && (
                <tr><td colSpan={9} className="px-5 py-8 text-center text-sm text-gray-400">Sin resultados.</td></tr>
              )}
              {items.map((p) => (
                <tr
                  key={p.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/products/${p.id}`)}
                >
                  <td className="px-5 py-3 font-mono text-xs text-gray-500">{p.sku_id}</td>
                  <td className="px-5 py-3 font-medium text-gray-800">{p.name}</td>
                  <td className="px-5 py-3 text-gray-500 text-xs">{p.family}</td>
                  <td className="px-5 py-3 text-gray-500">#{p.store_nbr}</td>
                  <td className="px-5 py-3 text-gray-700">${p.unit_cost.toLocaleString("es-CL")}</td>
                  <td className="px-5 py-3 text-gray-500">{p.lead_time_days}d</td>
                  <td className="px-5 py-3 text-gray-500">{p.min_order_qty}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      p.is_active ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500"
                    }`}>
                      {p.is_active ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td className="px-5 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => { setEditProduct(p); setShowForm(true); }}
                        className="p-1.5 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-700"
                        title="Editar"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      {p.is_active && (
                        <button
                          onClick={() => handleDeactivateClick(p)}
                          className="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-600"
                          title="Desactivar"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-gray-100 text-xs text-gray-500">
            <span>{data.total} productos · página {data.page} de {data.pages}</span>
            <div className="flex gap-1">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= (data?.pages ?? 1)}
                onClick={() => setPage((p) => p + 1)}
                className="p-1.5 rounded hover:bg-gray-100 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ProductFormModal */}
      {showForm && (
        <ProductFormModal
          product={editProduct}
          onClose={() => { setShowForm(false); setEditProduct(null); }}
          onSaved={() => {
            setShowForm(false);
            setEditProduct(null);
            queryClient.invalidateQueries({ queryKey: ["products"] });
          }}
        />
      )}

      {/* ConfirmModal — desactivar */}
      {deactivateTarget && (
        <ConfirmModal
          isOpen
          title={deactivateBlocked ? "No se puede desactivar" : "Desactivar producto"}
          message={
            deactivateBlocked
              ? `"${deactivateTarget.name}" tiene órdenes pendientes. Cancélalas antes de desactivar.`
              : `¿Desactivar "${deactivateTarget.name}" (${deactivateTarget.sku_id})? El producto no aparecerá en nuevas órdenes.`
          }
          confirmLabel="Desactivar"
          confirmClassName="bg-red-600 hover:bg-red-700 text-white"
          isLoading={deleteMutation.isPending}
          onConfirm={deactivateBlocked ? undefined : () => deleteMutation.mutate(deactivateTarget.id)}
          onClose={() => setDeactivateTarget(null)}
        />
      )}
    </div>
  );
}

// ─── SummaryCard ──────────────────────────────────────────────────────────────

function SummaryCard({
  label, value, icon, bg,
}: {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  bg: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${bg}`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-xs text-gray-400 font-medium">{label}</p>
      </div>
    </div>
  );
}
