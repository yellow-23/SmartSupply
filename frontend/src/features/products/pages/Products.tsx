import { useState } from "react";
import { Plus, Package, AlertTriangle, Pencil, Trash2, Loader2, X } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchProducts, createProduct, updateProduct, deleteProduct, Product, ProductCreate } from "../api/products";
import { listBusinesses } from "../../../shared/api/data";

const EMPTY_FORM: Omit<ProductCreate, "business_id"> = {
  store_nbr: 1, family: "", unit_cost: null,
  order_cost: null, holding_rate: null, lead_time_days: null, moq: null,
};

export default function Products() {
  const qc = useQueryClient();
  const [businessId, setBusinessId] = useState<number | null>(null);
  const [modal, setModal] = useState<"create" | "edit" | null>(null);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);

  const { data: businesses } = useQuery({
    queryKey: ["businesses"],
    queryFn: listBusinesses,
    staleTime: 60_000,
  });

  const { data: page, isLoading } = useQuery({
    queryKey: ["products", businessId],
    queryFn: () => fetchProducts({ business_id: businessId!, limit: 100 }),
    enabled: businessId != null,
    staleTime: 60_000,
  });

  const products = page?.items ?? [];

  const createMut = useMutation({
    mutationFn: (f: typeof EMPTY_FORM) => createProduct({ ...f, business_id: businessId! }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["products"] }); closeModal(); },
  });

  const updateMut = useMutation({
    mutationFn: ({ id, body }: { id: number; body: typeof EMPTY_FORM }) => updateProduct(id, body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["products"] }); closeModal(); },
  });

  const deleteMut = useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["products"] }); setDeleteTarget(null); },
  });

  function openCreate() { setForm(EMPTY_FORM); setEditing(null); setModal("create"); }

  function openEdit(p: Product) {
    setForm({ store_nbr: p.store_nbr, family: p.family, unit_cost: p.unit_cost, order_cost: p.order_cost, holding_rate: p.holding_rate, lead_time_days: p.lead_time_days, moq: p.moq });
    setEditing(p);
    setModal("edit");
  }

  function closeModal() { setModal(null); setEditing(null); }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (modal === "create") createMut.mutate(form);
    else if (editing) updateMut.mutate({ id: editing.id, body: form });
  }

  const mutError = (createMut.error || updateMut.error) as any;
  const isSaving = createMut.isPending || updateMut.isPending;
  const alertCount = products.filter(p => !p.unit_cost).length;
  const families = [...new Set(products.map(p => p.family))];

  return (
    <div className="space-y-6">
      {/* Business selector */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
        <label className="text-xs font-medium text-gray-500 block mb-1">Negocio</label>
        <select
          value={businessId ?? ""}
          onChange={e => setBusinessId(e.target.value ? Number(e.target.value) : null)}
          className="w-64 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30"
        >
          <option value="">Selecciona un negocio</option>
          {businesses?.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
      </div>

      {businessId == null ? (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-16 flex flex-col items-center text-gray-400">
          <Package className="w-10 h-10 mb-2 opacity-20" />
          <p className="text-sm">Elige un negocio para ver sus productos.</p>
        </div>
      ) : (<>

      {/* Summary cards */}
      <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
        {[
          { label: "Total familias",    value: String(page?.total_families ?? 0), icon: Package,       bg: "bg-blue-50",    text: "text-blue-900"   },
          { label: "Configuradas",      value: String(products.length),           icon: Package,       bg: "bg-emerald-50", text: "text-emerald-500" },
          { label: "Sin costo cargado", value: String(alertCount),                icon: AlertTriangle, bg: "bg-red-50",     text: "text-red-500"    },
        ].map(({ label, value, icon: Icon, bg, text }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center gap-4">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${bg}`}>
              <Icon className={`w-5 h-5 ${text}`} />
            </div>
            <div>
              {isLoading ? <div className="h-7 w-10 bg-gray-100 animate-pulse rounded" /> : <p className="text-2xl font-bold text-gray-900">{value}</p>}
              <p className="text-xs text-gray-400 font-medium">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50">
          <p className="text-sm text-gray-500">{products.length} familia{products.length !== 1 ? "s" : ""} configurada{products.length !== 1 ? "s" : ""}</p>
          <button
            onClick={openCreate}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nueva familia
          </button>
        </div>

        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-16 gap-2 text-gray-400">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-sm">Cargando productos...</span>
            </div>
          ) : products.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <Package className="w-10 h-10 mb-2 opacity-30" />
              <p className="text-sm">No hay productos registrados.</p>
              <button onClick={openCreate} className="mt-3 text-sm text-orange-600 hover:underline">Agregar el primero</button>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {["Familia", "Tienda", "Costo unit.", "Costo pedido", "Lead time", "MOQ", ""].map(h => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {products.map(p => (
                  <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-800">{p.family}</td>
                    <td className="px-6 py-4 text-gray-500">{p.store_nbr}</td>
                    <td className="px-6 py-4 text-gray-700">
                      {p.unit_cost ? `$${p.unit_cost.toLocaleString("es-CL")}` : <span className="text-red-400 text-xs">Sin costo</span>}
                    </td>
                    <td className="px-6 py-4 text-gray-500">${(p.order_cost ?? 5000).toLocaleString("es-CL")}</td>
                    <td className="px-6 py-4 text-gray-500">{p.lead_time_days}d</td>
                    <td className="px-6 py-4 text-gray-500">{p.moq ?? "—"}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 justify-end">
                        <button onClick={() => openEdit(p)} className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                        <button onClick={() => setDeleteTarget(p)} className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Create / Edit modal */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-base font-semibold text-gray-900">
                {modal === "create" ? "Nuevo producto" : "Editar producto"}
              </h2>
              <button onClick={closeModal} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-500">Familia</label>
                  <input
                    required
                    disabled={modal === "edit"}
                    value={form.family}
                    onChange={e => setForm(f => ({ ...f, family: e.target.value.toUpperCase() }))}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30 disabled:bg-gray-50 disabled:text-gray-400"
                    placeholder="BEBIDAS"
                    list="families-list"
                  />
                  <datalist id="families-list">
                    {families.map(fam => <option key={fam} value={fam} />)}
                  </datalist>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500">Tienda</label>
                  <input
                    required type="number" min={1} max={54}
                    disabled={modal === "edit"}
                    value={form.store_nbr}
                    onChange={e => setForm(f => ({ ...f, store_nbr: Number(e.target.value) }))}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30 disabled:bg-gray-50 disabled:text-gray-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-500">Costo unitario ($)</label>
                  <input
                    type="number" min={0} step={1}
                    value={form.unit_cost ?? ""}
                    onChange={e => setForm(f => ({ ...f, unit_cost: e.target.value ? Number(e.target.value) : null }))}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30"
                    placeholder="ej: 1200"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500">Costo por pedido ($)</label>
                  <input
                    type="number" min={0} step={100}
                    value={form.order_cost}
                    onChange={e => setForm(f => ({ ...f, order_cost: Number(e.target.value) }))}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-500">Lead time (días)</label>
                  <input
                    required type="number" min={1}
                    value={form.lead_time_days}
                    onChange={e => setForm(f => ({ ...f, lead_time_days: Number(e.target.value) }))}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500">MOQ (un.)</label>
                  <input
                    type="number" min={0}
                    value={form.moq ?? ""}
                    onChange={e => setForm(f => ({ ...f, moq: e.target.value ? Number(e.target.value) : null }))}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30"
                    placeholder="opcional"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500">Holding rate</label>
                  <input
                    required type="number" min={0} max={1} step={0.01}
                    value={form.holding_rate}
                    onChange={e => setForm(f => ({ ...f, holding_rate: Number(e.target.value) }))}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30"
                  />
                </div>
              </div>

              {mutError && (
                <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  {mutError.response?.data?.detail ?? "Error al guardar"}
                </p>
              )}

              <div className="flex justify-end gap-2 pt-1">
                <button type="button" onClick={closeModal} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 disabled:opacity-60 transition-colors"
                >
                  {isSaving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  {modal === "create" ? "Crear" : "Guardar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirm */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm mx-4 p-6">
            <h2 className="text-base font-semibold text-gray-900 mb-1">Eliminar producto</h2>
            <p className="text-sm text-gray-500 mb-5">
              ¿Seguro que quieres eliminar <span className="font-medium text-gray-800">{deleteTarget.family}</span>? Esta acción no se puede deshacer.
            </p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setDeleteTarget(null)} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
                Cancelar
              </button>
              <button
                onClick={() => deleteMut.mutate(deleteTarget.id)}
                disabled={deleteMut.isPending}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:opacity-90 disabled:opacity-60 transition-colors"
              >
                {deleteMut.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
      </>)}
    </div>
  );
}
