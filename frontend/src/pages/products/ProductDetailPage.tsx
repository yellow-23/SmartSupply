import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Package, AlertTriangle } from "lucide-react";
import { useForm, type Resolver } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import api from "../../api/axios.instance";
import type { ProductResponse } from "../../types/product";

// ─── Supplier schema ──────────────────────────────────────────────────────────

const supplierSchema = z.object({
  supplier_name: z.string().min(1, "Requerido"),
  lead_time_days: z.coerce.number().int().gt(0, "Debe ser mayor a 0"),
  min_order_qty: z.coerce.number().int().gt(0, "Debe ser mayor a 0"),
  pack_size: z.coerce.number().int().gt(0, "Debe ser mayor a 0"),
});
type SupplierValues = z.infer<typeof supplierSchema>;

// ─── Types ────────────────────────────────────────────────────────────────────

interface AlertItem {
  sku_id: string;
  reorder_point_s: number;
}

// ─── Componente ───────────────────────────────────────────────────────────────

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"info" | "supplier">("info");

  // Product data
  const { data: product, isLoading, isError } = useQuery<ProductResponse>({
    queryKey: ["product", id],
    queryFn: async () => {
      const { data } = await api.get(`/products/${id}`);
      return data;
    },
    enabled: !!id,
  });

  // Inventory alerts — to compare MOQ vs reorder point S
  const { data: alertsData } = useQuery<{ alerts: AlertItem[] }>({
    queryKey: ["inventory", "alerts", 50],
    queryFn: async () => {
      const { data } = await api.get("/inventory/alerts?limit=50&sort_by=urgency");
      return data;
    },
    enabled: !!product,
    staleTime: 300_000,
  });

  const reorderPoint = alertsData?.alerts.find((a) => a.sku_id === product?.sku_id)?.reorder_point_s;
  const moqExceedsReorder =
    product !== undefined &&
    reorderPoint !== undefined &&
    product.min_order_qty > reorderPoint;

  // Supplier form
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SupplierValues>({
    resolver: zodResolver(supplierSchema) as Resolver<SupplierValues>,
    defaultValues: { supplier_name: "", lead_time_days: 3, min_order_qty: 1, pack_size: 1 },
  });

  useEffect(() => {
    if (product) {
      reset({
        supplier_name: product.supplier_name ?? "",
        lead_time_days: product.lead_time_days,
        min_order_qty: product.min_order_qty,
        pack_size: product.pack_size,
      });
    }
  }, [product, reset]);

  const supplierMutation = useMutation({
    mutationFn: (data: SupplierValues) => api.patch(`/products/${id}/supplier`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["product", id] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
    },
  });

  // ─── Render ──────────────────────────────────────────────────────────────────

  if (isLoading) {
    return <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Cargando…</div>;
  }

  if (isError || !product) {
    return (
      <div className="flex flex-col items-center justify-center h-48 gap-2">
        <p className="text-red-500 text-sm">Producto no encontrado.</p>
        <button onClick={() => navigate("/products")} className="text-xs text-primary hover:underline">
          ← Volver al listado
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate("/products")}
          className="p-2 rounded-lg hover:bg-gray-100 text-gray-500"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
          <Package className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-gray-900">{product.name}</h2>
          <p className="text-xs text-gray-400 font-mono">{product.sku_id}</p>
        </div>
        <span className={`ml-auto inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
          product.is_active ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500"
        }`}>
          {product.is_active ? "Activo" : "Inactivo"}
        </span>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex border-b border-gray-100">
          {(["info", "supplier"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? "border-orange-500 text-orange-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab === "info" ? "Información" : "Proveedor"}
            </button>
          ))}
        </div>

        {/* Tab: Información */}
        {activeTab === "info" && (
          <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <InfoField label="SKU" value={product.sku_id} mono />
            <InfoField label="Familia" value={product.family} />
            <InfoField label="Tienda" value={`#${product.store_nbr}`} />
            <InfoField label="Costo unitario" value={`$${product.unit_cost.toLocaleString("es-CL")}`} />
            <InfoField label="Lead time" value={`${product.lead_time_days} días`} />
            <InfoField label="Costo por orden" value={`$${product.order_cost.toLocaleString("es-CL")}`} />
            <InfoField label="Tasa de mantención" value={`${(product.holding_cost_pct * 100).toFixed(1)}%`} />
            <InfoField label="MOQ" value={String(product.min_order_qty)} />
            <InfoField label="Tamaño pack" value={String(product.pack_size)} />
            <InfoField label="Proveedor" value={product.supplier_name ?? "—"} />
            <InfoField label="Creado" value={new Date(product.created_at).toLocaleDateString("es-CL")} />
            <InfoField label="Actualizado" value={new Date(product.updated_at).toLocaleDateString("es-CL")} />
          </div>
        )}

        {/* Tab: Proveedor */}
        {activeTab === "supplier" && (
          <form
            onSubmit={handleSubmit((data) => supplierMutation.mutate(data))}
            className="p-6 space-y-5 max-w-lg"
          >
            {moqExceedsReorder && (
              <div className="flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-700">
                <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>
                  El MOQ ({product.min_order_qty} u.) supera el punto de reorden S ({reorderPoint} u.).
                  Las órdenes de reabastecimiento podrían exceder la capacidad recomendada.
                </span>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Nombre del proveedor" error={errors.supplier_name?.message} className="sm:col-span-2">
                <input
                  {...register("supplier_name")}
                  placeholder="Distribuidora XYZ"
                  className={fieldCls(!!errors.supplier_name)}
                />
              </Field>

              <Field label="Lead time (días)" error={errors.lead_time_days?.message}>
                <input
                  {...register("lead_time_days")}
                  type="number"
                  min={1}
                  className={fieldCls(!!errors.lead_time_days)}
                />
              </Field>

              <Field label="MOQ (mín. de compra)" error={errors.min_order_qty?.message}>
                <input
                  {...register("min_order_qty")}
                  type="number"
                  min={1}
                  className={fieldCls(!!errors.min_order_qty)}
                />
              </Field>

              <Field label="Tamaño pack" error={errors.pack_size?.message}>
                <input
                  {...register("pack_size")}
                  type="number"
                  min={1}
                  className={fieldCls(!!errors.pack_size)}
                />
              </Field>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={supplierMutation.isPending}
                className="px-5 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 disabled:opacity-60 font-medium"
              >
                {supplierMutation.isPending ? "Guardando…" : "Guardar proveedor"}
              </button>
              {supplierMutation.isSuccess && (
                <span className="text-xs text-emerald-600">✓ Guardado correctamente</span>
              )}
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function InfoField({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <p className="text-xs text-gray-400 font-medium mb-1">{label}</p>
      <p className={`text-sm text-gray-800 font-medium ${mono ? "font-mono" : ""}`}>{value}</p>
    </div>
  );
}

function Field({
  label, error, children, className = "",
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      <label className="block text-xs font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}

function fieldCls(hasError: boolean) {
  return [
    "w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30",
    hasError ? "border-red-300 focus:border-red-500" : "border-gray-200 focus:border-primary",
  ].join(" ");
}
