import { useEffect, useState } from "react";
import BrandLoader from "../../../shared/ui/BrandLoader";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Check, Loader2, MapPin, Pencil, Plus, X } from "lucide-react";
import { useAuthStore, useActiveBusinessId, useActiveStoreNbr } from "../../auth/store/authStore";
import {
  Business, BusinessInput, BUSINESS_FORM_FIELDS, STORE_FORM_FIELDS, StoreItem,
  createBusiness, createBusinessStore, listBusinesses, listBusinessStores, updateBusiness, updateBusinessStore,
} from "../../../shared/api/data";
import FormModal from "../../../shared/ui/FormModal";
import { toast } from "../../../shared/ui/toastStore";

const FIELDS: { name: keyof BusinessInput; label: string; placeholder: string; type?: string; hint?: string }[] = [
  { name: "name", label: "Nombre o razón social", placeholder: "Distribuidora El Roble SpA" },
  { name: "rut", label: "RUT", placeholder: "76.123.456-7", hint: "Se valida el dígito verificador." },
  { name: "city", label: "Ciudad / comuna", placeholder: "Ñuñoa" },
  { name: "address", label: "Dirección", placeholder: "Av. Grecia 1234" },
  { name: "phone", label: "Teléfono", placeholder: "+56 9 1234 5678", type: "tel" },
  { name: "email", label: "Correo de compras", placeholder: "compras@elroble.cl", type: "email" },
];

const input =
  "mt-1 w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30 disabled:bg-gray-50 disabled:text-gray-500";
const errorOf = (e: unknown) => (e as any)?.response?.data?.detail ?? "No se pudo guardar";

export default function BusinessPage() {
  const qc = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const businessId = useActiveBusinessId();
  const activeStoreNbr = useActiveStoreNbr();
  const setActiveBusiness = useAuthStore((s) => s.setActiveBusiness);
  const setActiveStore = useAuthStore((s) => s.setActiveStore);
  const [creatingBusiness, setCreatingBusiness] = useState(false);
  const [creatingStore, setCreatingStore] = useState(false);

  const businesses = useQuery({ queryKey: ["businesses", user?.id], queryFn: listBusinesses, enabled: !!user });
  const business = businesses.data?.find((b) => b.id === businessId);
  const canEdit = user?.role === "platform_admin" || business?.my_role === "owner";

  const stores = useQuery({
    queryKey: ["stores", businessId],
    queryFn: () => listBusinessStores(businessId!),
    enabled: businessId != null,
  });

  const refreshBusinesses = () => qc.invalidateQueries({ queryKey: ["businesses"] });

  const newBusiness = useMutation({
    mutationFn: (v: Record<string, string>) => createBusiness(v as BusinessInput & { name: string }),
    onSuccess: (b) => {
      refreshBusinesses();
      setActiveBusiness(b.id);
      toast.success(`${b.name} creado. Ahora estás trabajando en él.`);
    },
  });

  const newStore = useMutation({
    mutationFn: (v: Record<string, string>) => createBusinessStore(businessId!, v as { name: string }),
    onSuccess: (s) => {
      qc.invalidateQueries({ queryKey: ["stores", businessId] });
      setActiveStore(s.store_nbr);
      toast.success(`Ubicación ${s.name} creada`);
    },
  });

  if (!business) {
    return (
      <BrandLoader label="Cargando tu negocio..." className="min-h-[50vh]" />
    );
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <BusinessForm key={business.id} business={business} canEdit={canEdit} onSaved={refreshBusinesses} />

      <section className="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">Ubicaciones</h2>
            <p className="text-xs text-gray-400">Bodegas o sucursales. Cada una tiene su propio stock, inventario y órdenes.</p>
          </div>
          {canEdit && (
            <button onClick={() => setCreatingStore(true)} className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50">
              <Plus className="w-4 h-4" /> Nueva ubicación
            </button>
          )}
        </div>
        <ul className="divide-y divide-gray-50">
          {(stores.data ?? []).map((s) => (
            <StoreRow
              key={s.store_nbr}
              store={s}
              businessId={business.id}
              canEdit={canEdit}
              active={s.store_nbr === activeStoreNbr}
              onUse={() => setActiveStore(s.store_nbr)}
            />
          ))}
        </ul>
      </section>

      <section className="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">Tus negocios</h2>
            <p className="text-xs text-gray-400">Todo en SmartSupply (ventas, inventario, órdenes) se ve por el negocio activo.</p>
          </div>
          <button onClick={() => setCreatingBusiness(true)} className="flex items-center gap-2 px-3 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90">
            <Plus className="w-4 h-4" /> Nuevo negocio
          </button>
        </div>
        <ul className="divide-y divide-gray-50">
          {(businesses.data ?? []).map((b) => (
            <li key={b.id} className="flex items-center justify-between gap-3 px-6 py-3">
              <div className="flex items-center gap-3 min-w-0">
                <Building2 className="w-4 h-4 text-gray-400 shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{b.name}</p>
                  <p className="text-xs text-gray-400 truncate">
                    {[b.rut ?? "Sin RUT", b.city, b.my_role === "owner" ? "Dueño" : "Miembro"].filter(Boolean).join(" · ")}
                  </p>
                </div>
              </div>
              {b.id === businessId ? (
                <span className="flex items-center gap-1 text-xs font-medium text-emerald-600"><Check className="w-3.5 h-3.5" /> Activo</span>
              ) : (
                <button onClick={() => setActiveBusiness(b.id)} className="px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50">
                  Trabajar en este
                </button>
              )}
            </li>
          ))}
        </ul>
      </section>

      <FormModal
        open={creatingBusiness}
        title="Nuevo negocio"
        description="Se crea con una ubicación 'Tienda Principal' y queda como negocio activo."
        fields={BUSINESS_FORM_FIELDS}
        submitLabel="Crear negocio"
        onSubmit={(v) => newBusiness.mutateAsync(v)}
        onClose={() => setCreatingBusiness(false)}
      />
      <FormModal
        open={creatingStore}
        title="Nueva ubicación"
        description={`Se agrega a ${business.name}.`}
        fields={STORE_FORM_FIELDS}
        submitLabel="Crear ubicación"
        onSubmit={(v) => newStore.mutateAsync(v)}
        onClose={() => setCreatingStore(false)}
      />
    </div>
  );
}

function BusinessForm({ business, canEdit, onSaved }: { business: Business; canEdit: boolean; onSaved: () => void }) {
  const initial = Object.fromEntries(FIELDS.map((f) => [f.name, business[f.name] ?? ""])) as Record<keyof BusinessInput, string>;
  const [form, setForm] = useState(initial);
  useEffect(() => setForm(initial), [business]);
  const dirty = FIELDS.some((f) => form[f.name] !== initial[f.name]);

  const save = useMutation({
    mutationFn: () => updateBusiness(business.id, form),
    onSuccess: (b) => {
      onSaved();
      toast.success("Datos del negocio guardados");
      setForm(Object.fromEntries(FIELDS.map((f) => [f.name, b[f.name] ?? ""])) as typeof form);
    },
  });
  const missing = !business.rut || !business.city || !business.address;

  return (
    <section className="bg-white rounded-xl border border-gray-100 shadow-sm">
      <div className="px-6 py-4 border-b border-gray-50">
        <h2 className="text-sm font-semibold text-gray-800">Datos de la empresa</h2>
        <p className="text-xs text-gray-400">Aparecen como comprador en el PDF de cada orden de compra.</p>
      </div>
      <form
        className="p-6 space-y-4"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        {missing && canEdit && (
          <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
            Completa RUT, ciudad y dirección: tus proveedores los necesitan en la orden de compra.
          </p>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {FIELDS.map((f) => (
            <label key={f.name} className="block">
              <span className="text-xs font-medium text-gray-500">{f.label}</span>
              <input
                type={f.type ?? "text"}
                value={form[f.name]}
                onChange={(e) => setForm((s) => ({ ...s, [f.name]: e.target.value }))}
                placeholder={f.placeholder}
                disabled={!canEdit}
                required={f.name === "name"}
                className={input}
              />
              {f.hint && <span className="text-[11px] text-gray-400">{f.hint}</span>}
            </label>
          ))}
        </div>
        {save.error && <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">{errorOf(save.error)}</p>}
        {canEdit ? (
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!dirty || save.isPending}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 disabled:opacity-50"
            >
              {save.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Guardar cambios
            </button>
          </div>
        ) : (
          <p className="text-xs text-gray-400">Solo el dueño del negocio puede editar estos datos.</p>
        )}
      </form>
    </section>
  );
}

function StoreRow({ store, businessId, canEdit, active, onUse }: {
  store: StoreItem; businessId: number; canEdit: boolean; active: boolean; onUse: () => void;
}) {
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(store.name ?? "");
  const [city, setCity] = useState(store.city ?? "");

  const save = useMutation({
    mutationFn: () => updateBusinessStore(businessId, store.store_nbr, { name, city: city || null }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["stores", businessId] });
      setEditing(false);
    },
  });

  return (
    <li className="flex items-center justify-between gap-3 px-6 py-3">
      {editing ? (
        <form
          className="flex flex-wrap items-center gap-2 flex-1"
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
        >
          <input value={name} onChange={(e) => setName(e.target.value)} required aria-label="Nombre de la ubicación" className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg" />
          <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Ciudad" aria-label="Ciudad" className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg" />
          <button type="submit" disabled={save.isPending} className="px-3 py-1.5 text-xs bg-orange-600 text-white rounded-lg disabled:opacity-60">Guardar</button>
          <button type="button" onClick={() => setEditing(false)} aria-label="Cancelar" className="p-1.5 text-gray-400 hover:bg-gray-100 rounded-lg"><X className="w-4 h-4" /></button>
          {save.error && <span className="text-xs text-red-600">{errorOf(save.error)}</span>}
        </form>
      ) : (
        <div className="flex items-center gap-3 min-w-0">
          <MapPin className="w-4 h-4 text-gray-400 shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">{store.name || `Ubicación ${store.store_nbr}`}</p>
            <p className="text-xs text-gray-400">{store.city ?? "Sin ciudad"} · N° {store.store_nbr}</p>
          </div>
        </div>
      )}
      {!editing && (
        <div className="flex items-center gap-2 shrink-0">
          {active ? (
            <span className="flex items-center gap-1 text-xs font-medium text-emerald-600"><Check className="w-3.5 h-3.5" /> Activa</span>
          ) : (
            <button onClick={onUse} className="px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-gray-50">Usar esta</button>
          )}
          {canEdit && (
            <button onClick={() => setEditing(true)} aria-label="Editar ubicación" className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg">
              <Pencil className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}
    </li>
  );
}
