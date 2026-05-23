import { useEffect, useState } from "react";
import { useForm, type Resolver } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { X } from "lucide-react";
import { useMutation } from "@tanstack/react-query";
import api from "../../api/axios.instance";
import type { ProductResponse } from "../../types/product";
import { PRODUCT_FAMILIES } from "../../constants/families";

// ─── Schema ───────────────────────────────────────────────────────────────────

const formSchema = z.object({
  sku_id: z.string().min(1, "Requerido"),
  name: z.string().min(1, "Requerido"),
  family: z.string().min(1, "Selecciona una familia"),
  store_nbr: z.coerce.number().int().min(1, "Mínimo 1"),
  unit_cost: z.coerce.number().gt(0, "Debe ser mayor a 0"),
  lead_time_days: z.coerce.number().int().gt(0, "Debe ser mayor a 0"),
  order_cost: z.coerce.number().gte(0, "Debe ser >= 0"),
  holding_cost_pct: z.coerce.number().gt(0, "Debe ser mayor a 0").max(100, "Máximo 100%"),
  min_order_qty: z.coerce.number().int().gt(0, "Debe ser mayor a 0"),
  pack_size: z.coerce.number().int().gt(0, "Debe ser mayor a 0"),
  supplier_name: z.string().optional(),
  demand_preview: z.coerce.number().int().min(1, "Mínimo 1"),
});

type FormValues = z.infer<typeof formSchema>;

// ─── Props ────────────────────────────────────────────────────────────────────

interface Props {
  product: ProductResponse | null;
  onClose: () => void;
  onSaved: () => void;
}

// ─── Componente ───────────────────────────────────────────────────────────────

export default function ProductFormModal({ product, onClose, onSaved }: Props) {
  const isEdit = product !== null;
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    reset,
    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema) as Resolver<FormValues>,
    defaultValues: {
      sku_id: "",
      name: "",
      family: "",
      store_nbr: 1,
      unit_cost: 0,
      lead_time_days: 3,
      order_cost: 0,
      holding_cost_pct: 20,
      min_order_qty: 1,
      pack_size: 1,
      supplier_name: "",
      demand_preview: 1000,
    },
  });

  useEffect(() => {
    if (product) {
      reset({
        sku_id: product.sku_id,
        name: product.name,
        family: product.family,
        store_nbr: product.store_nbr,
        unit_cost: product.unit_cost,
        lead_time_days: product.lead_time_days,
        order_cost: product.order_cost,
        holding_cost_pct: +(product.holding_cost_pct * 100).toFixed(2),
        min_order_qty: product.min_order_qty,
        pack_size: product.pack_size,
        supplier_name: product.supplier_name ?? "",
        demand_preview: 1000,
      });
    }
  }, [product, reset]);

  // EOQ preview — Q* = √(2·D·S / H)
  const [unit_cost, order_cost, holding_cost_pct, demand_preview] = watch([
    "unit_cost", "order_cost", "holding_cost_pct", "demand_preview",
  ]);
  const H = (holding_cost_pct / 100) * unit_cost;
  const eoqPreview =
    order_cost > 0 && H > 0 && demand_preview > 0
      ? Math.round(Math.sqrt((2 * demand_preview * order_cost) / H))
      : null;

  const mutation = useMutation({
    mutationFn: async (data: FormValues) => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { demand_preview: _demand, sku_id, ...rest } = data;
      const payload = { ...rest, holding_cost_pct: rest.holding_cost_pct / 100 };
      if (isEdit) {
        return api.patch(`/products/${product!.id}`, payload);
      }
      return api.post("/products", { sku_id, ...payload });
    },
    onSuccess: onSaved,
    onError: (err: unknown) => {
      const status = (err as { response?: { status?: number; data?: { detail?: string } } })?.response?.status;
      if (status === 409) {
        setError("sku_id", { message: "Este SKU ya existe" });
      } else {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setServerError(detail ?? "Error al guardar. Intenta nuevamente.");
      }
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 sticky top-0 bg-white z-10">
          <h3 className="text-base font-semibold text-gray-900">
            {isEdit ? `Editar — ${product!.sku_id}` : "Nuevo producto"}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit((d) => { setServerError(null); mutation.mutate(d); })} className="p-6 space-y-5">
          {serverError && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {serverError}
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

            <Field label="SKU" error={errors.sku_id?.message}>
              <input
                {...register("sku_id")}
                disabled={isEdit}
                placeholder="GROCERY-001"
                className={fieldCls(!!errors.sku_id, isEdit)}
              />
            </Field>

            <Field label="Nombre" error={errors.name?.message}>
              <input {...register("name")} placeholder="Arroz 1kg" className={fieldCls(!!errors.name)} />
            </Field>

            <Field label="Familia" error={errors.family?.message}>
              <select {...register("family")} className={fieldCls(!!errors.family)}>
                <option value="">Seleccionar…</option>
                {PRODUCT_FAMILIES.map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
            </Field>

            <Field label="Tienda N°" error={errors.store_nbr?.message}>
              <input {...register("store_nbr")} type="number" min={1} max={54} className={fieldCls(!!errors.store_nbr)} />
            </Field>

            <Field label="Costo unitario (CLP)" error={errors.unit_cost?.message}>
              <input {...register("unit_cost")} type="number" step="0.01" min={0} className={fieldCls(!!errors.unit_cost)} />
            </Field>

            <Field label="Lead time (días)" error={errors.lead_time_days?.message}>
              <input {...register("lead_time_days")} type="number" min={1} className={fieldCls(!!errors.lead_time_days)} />
            </Field>

            <Field label="Costo por orden (CLP)" error={errors.order_cost?.message}>
              <input {...register("order_cost")} type="number" step="0.01" min={0} className={fieldCls(!!errors.order_cost)} />
            </Field>

            <Field label="Tasa de mantención (%/año)" error={errors.holding_cost_pct?.message}>
              <input {...register("holding_cost_pct")} type="number" step="0.1" min={0.1} className={fieldCls(!!errors.holding_cost_pct)} />
            </Field>

            <Field label="MOQ (mín. de compra)" error={errors.min_order_qty?.message}>
              <input {...register("min_order_qty")} type="number" min={1} className={fieldCls(!!errors.min_order_qty)} />
            </Field>

            <Field label="Tamaño pack" error={errors.pack_size?.message}>
              <input {...register("pack_size")} type="number" min={1} className={fieldCls(!!errors.pack_size)} />
            </Field>

            <Field label="Proveedor (opcional)" error={errors.supplier_name?.message} className="sm:col-span-2">
              <input {...register("supplier_name")} placeholder="Distribuidora XYZ" className={fieldCls(!!errors.supplier_name)} />
            </Field>
          </div>

          {/* EOQ Preview */}
          <div className="rounded-xl bg-blue-50 border border-blue-100 p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-blue-800">Vista previa EOQ (Q*)</span>
              <span className="text-xl font-bold text-blue-900">
                {eoqPreview !== null ? `${eoqPreview.toLocaleString("es-CL")} u.` : "—"}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-blue-600">
              <span>Demanda anual estimada (u.):</span>
              <input
                {...register("demand_preview")}
                type="number"
                min={1}
                className="w-24 px-2 py-1 rounded border border-blue-200 bg-white text-gray-800 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
            </div>
            <p className="text-xs text-blue-500 mt-2">
              Q* = √(2·D·S / H) — solo informativo, no se guarda
            </p>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="px-5 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 disabled:opacity-60 font-medium"
            >
              {mutation.isPending ? "Guardando…" : isEdit ? "Guardar cambios" : "Crear producto"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function Field({
  label,
  error,
  children,
  className = "",
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

function fieldCls(hasError: boolean, disabled = false) {
  return [
    "w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30",
    hasError ? "border-red-300 focus:border-red-500" : "border-gray-200 focus:border-primary",
    disabled ? "bg-gray-50 text-gray-500 cursor-not-allowed" : "bg-white",
  ].join(" ");
}
