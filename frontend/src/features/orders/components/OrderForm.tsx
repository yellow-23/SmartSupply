import { useMemo, useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Plus, Trash2, X, Loader2 } from 'lucide-react';
import Modal from '../../../shared/ui/Modal';
import { fetchProducts } from '../../products/api/products';
import { createOrder, updateOrder, PurchaseOrder } from '../api/orders';

interface Line {
  family: string;
  quantity: string;
  unit_cost: string;
}

interface Props {
  open: boolean;
  businessId: number;
  storeNbr: number;
  order?: PurchaseOrder | null; // si viene, es edicion
  draft?: { supplier: string | null; lines: { family: string; quantity: number; unit_cost: number | null }[] }; // OC nueva precompletada
  onClose: () => void;
  onSaved: (order: PurchaseOrder) => void;
}

const EMPTY_LINE: Line = { family: '', quantity: '', unit_cost: '' };
const fmtCLP = (n: number) => `$${Math.round(n).toLocaleString('es-CL')}`;
const input = 'w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30';

export default function OrderForm({ open, businessId, storeNbr, order, draft, onClose, onSaved }: Props) {
  return (
    <Modal open={open} onClose={onClose} className="max-w-3xl">
      {/* Se monta de nuevo en cada apertura para partir con el estado de la orden actual */}
      {open && (
        <FormBody businessId={businessId} storeNbr={order?.store_nbr ?? storeNbr} order={order} draft={draft} onClose={onClose} onSaved={onSaved} />
      )}
    </Modal>
  );
}

function FormBody({ businessId, storeNbr, order, draft, onClose, onSaved }: Omit<Props, 'open'>) {
  const [supplier, setSupplier] = useState(order?.supplier ?? draft?.supplier ?? '');
  const [delivery, setDelivery] = useState(order?.expected_delivery ?? '');
  const [lines, setLines] = useState<Line[]>(() => {
    const source = order?.lines ?? draft?.lines;
    return source
      ? source.map((l) => ({ family: l.family, quantity: String(l.quantity), unit_cost: l.unit_cost != null ? String(l.unit_cost) : '' }))
      : [{ ...EMPTY_LINE }];
  });

  const { data: page } = useQuery({
    queryKey: ['products', businessId, 'order-form'],
    queryFn: () => fetchProducts({ business_id: businessId, store_nbr: storeNbr, limit: 100 }),
  });
  const products = page?.items ?? [];
  const suppliers = [...new Set(products.map((p) => p.supplier).filter(Boolean))] as string[];

  // Con proveedor elegido se muestran primero sus productos; el resto sigue disponible
  const options = useMemo(() => {
    const s = supplier.trim().toLowerCase();
    return [...products].sort((a, b) => {
      const ma = s && a.supplier?.toLowerCase() === s ? 0 : 1;
      const mb = s && b.supplier?.toLowerCase() === s ? 0 : 1;
      return ma - mb || a.family.localeCompare(b.family);
    });
  }, [products, supplier]);

  const setLine = (i: number, patch: Partial<Line>) =>
    setLines((ls) => ls.map((l, j) => (j === i ? { ...l, ...patch } : l)));

  const pickProduct = (i: number, family: string) => {
    const p = products.find((x) => x.family === family);
    setLine(i, { family, unit_cost: p?.unit_cost != null ? String(p.unit_cost) : '' });
    if (p?.supplier && !supplier) setSupplier(p.supplier);
  };

  const total = lines.reduce((acc, l) => acc + (Number(l.quantity) || 0) * (Number(l.unit_cost) || 0), 0);
  const chosen = lines.map((l) => l.family).filter(Boolean);
  const valid = lines.length > 0 && lines.every((l) => l.family && Number(l.quantity) > 0) && new Set(chosen).size === chosen.length;

  const save = useMutation({
    mutationFn: () => {
      const body = {
        supplier: supplier.trim() || null,
        expected_delivery: delivery || null,
        lines: lines.map((l) => ({
          family: l.family,
          quantity: Number(l.quantity),
          unit_cost: l.unit_cost === '' ? null : Number(l.unit_cost),
        })),
      };
      return order ? updateOrder(order.id, businessId, body) : createOrder(businessId, storeNbr, body);
    },
    onSuccess: onSaved,
  });
  const error = (save.error as any)?.response?.data?.detail;

  return (
    <form
      className="p-6 space-y-5"
      onSubmit={(e) => {
        e.preventDefault();
        if (valid) save.mutate();
      }}
    >
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-900">
          {order ? `Editar ${order.order_number}` : 'Nueva orden de compra'}
        </h2>
        <button type="button" onClick={onClose} aria-label="Cerrar" className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="block">
          <span className="text-xs font-medium text-gray-500">Proveedor</span>
          <input
            value={supplier}
            onChange={(e) => setSupplier(e.target.value)}
            list="order-suppliers"
            placeholder="Ej: Embotelladora Andina"
            className={`mt-1 ${input}`}
          />
          <datalist id="order-suppliers">
            {suppliers.map((s) => <option key={s} value={s} />)}
          </datalist>
        </label>
        <label className="block">
          <span className="text-xs font-medium text-gray-500">Entrega esperada</span>
          <input type="date" value={delivery} onChange={(e) => setDelivery(e.target.value)} className={`mt-1 ${input}`} />
          <span className="text-[11px] text-gray-400">Si la dejas vacía se calcula con el lead time más largo de los productos.</span>
        </label>
      </div>

      <div>
        <div className="grid grid-cols-[1fr_90px_110px_100px_32px] gap-2 text-xs font-semibold text-gray-400 uppercase tracking-wider pb-1">
          <span>Producto</span><span>Cantidad</span><span>Costo unit.</span><span className="text-right">Subtotal</span><span />
        </div>
        <div className="space-y-2">
          {lines.map((l, i) => (
            <div key={i} className="grid grid-cols-[1fr_90px_110px_100px_32px] gap-2 items-center">
              <select
                value={l.family}
                onChange={(e) => pickProduct(i, e.target.value)}
                aria-label={`Producto línea ${i + 1}`}
                className={input}
              >
                <option value="">Selecciona un producto</option>
                {options.map((p) => (
                  <option key={p.id} value={p.family} disabled={chosen.includes(p.family) && p.family !== l.family}>
                    {p.family}{p.supplier ? ` · ${p.supplier}` : ''}
                  </option>
                ))}
              </select>
              <input
                type="number" min={1} step={1}
                value={l.quantity}
                onChange={(e) => setLine(i, { quantity: e.target.value })}
                aria-label={`Cantidad línea ${i + 1}`}
                className={input}
              />
              <input
                type="number" min={0} step={1}
                value={l.unit_cost}
                onChange={(e) => setLine(i, { unit_cost: e.target.value })}
                placeholder="del catálogo"
                aria-label={`Costo unitario línea ${i + 1}`}
                className={input}
              />
              <span className="text-sm text-gray-700 text-right">
                {l.unit_cost && l.quantity ? fmtCLP(Number(l.unit_cost) * Number(l.quantity)) : '—'}
              </span>
              <button
                type="button"
                onClick={() => setLines((ls) => ls.filter((_, j) => j !== i))}
                disabled={lines.length === 1}
                aria-label={`Quitar línea ${i + 1}`}
                className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg disabled:opacity-30"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setLines((ls) => [...ls, { ...EMPTY_LINE }])}
          className="mt-3 flex items-center gap-1.5 text-sm text-orange-600 hover:underline"
        >
          <Plus className="w-4 h-4" /> Agregar producto
        </button>
        {products.length === 0 && (
          <p className="mt-2 text-xs text-amber-600">No hay productos en el catálogo de esta ubicación. Cárgalos en Ingesta o Productos.</p>
        )}
      </div>

      <div className="flex items-center justify-between border-t border-gray-100 pt-4">
        <p className="text-sm text-gray-500">
          Total <span className="font-semibold text-gray-900 text-base ml-1">{fmtCLP(total)}</span>
        </p>
        <div className="flex gap-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg">
            Cancelar
          </button>
          <button
            type="submit"
            disabled={!valid || save.isPending}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 disabled:opacity-50"
          >
            {save.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
            {order ? 'Guardar cambios' : 'Crear orden'}
          </button>
        </div>
      </div>
      {error && <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
    </form>
  );
}
