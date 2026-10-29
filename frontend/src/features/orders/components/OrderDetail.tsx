import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { X, Check, Download, Pencil, Loader2, Ban } from 'lucide-react';
import Modal from '../../../shared/ui/Modal';
import { downloadBlob } from '../../../shared/lib/utils';
import { toast } from '../../../shared/ui/toastStore';
import { downloadOrderPdf, updateOrderStatus, PurchaseOrder } from '../api/orders';

const STEPS: { status: PurchaseOrder['status']; label: string }[] = [
  { status: 'pending', label: 'Pendiente' },
  { status: 'confirmed', label: 'Confirmada' },
  { status: 'in_transit', label: 'En tránsito' },
  { status: 'received', label: 'Recibida' },
];

const NEXT: Partial<Record<PurchaseOrder['status'], { status: PurchaseOrder['status']; label: string; hint: string }>> = {
  pending: { status: 'confirmed', label: 'Confirmar orden', hint: 'El proveedor aceptó el pedido.' },
  confirmed: { status: 'in_transit', label: 'Marcar en tránsito', hint: 'El proveedor despachó.' },
  in_transit: { status: 'received', label: 'Marcar recibida', hint: 'Suma las cantidades al stock de cada producto.' },
};

const fmtCLP = (n: number) => `$${Math.round(n).toLocaleString('es-CL')}`;
const fmtDate = (s: string | null) =>
  s ? new Date(s.length === 10 ? `${s}T12:00:00` : s).toLocaleDateString('es-CL', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';

interface Props {
  order: PurchaseOrder | null;
  businessId: number;
  onClose: () => void;
  onEdit: (order: PurchaseOrder) => void;
  onChanged: (order: PurchaseOrder) => void;
}

export default function OrderDetail({ order, businessId, onClose, onEdit, onChanged }: Props) {
  return (
    <Modal open={!!order} onClose={onClose} className="max-w-3xl">
      {order && <DetailBody key={order.id} order={order} businessId={businessId} onClose={onClose} onEdit={onEdit} onChanged={onChanged} />}
    </Modal>
  );
}

function DetailBody({ order, businessId, onClose, onEdit, onChanged }: Props & { order: PurchaseOrder }) {
  const [confirmCancel, setConfirmCancel] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const status = useMutation({
    mutationFn: (newStatus: string) => updateOrderStatus(order.id, businessId, newStatus),
    onSuccess: (o) => {
      onChanged(o);
      setConfirmCancel(false);
      toast.success(o.status === 'received' ? 'Orden recibida: stock actualizado' : 'Estado actualizado');
    },
  });

  const pdf = async () => {
    setDownloading(true);
    try {
      downloadBlob(await downloadOrderPdf(order.id, businessId), `${order.order_number}.pdf`);
    } finally {
      setDownloading(false);
    }
  };

  const next = NEXT[order.status];
  const stepIdx = STEPS.findIndex((s) => s.status === order.status);
  const cancelled = order.status === 'cancelled';
  const canCancel = ['pending', 'confirmed', 'in_transit'].includes(order.status);
  const error = (status.error as any)?.response?.data?.detail;

  return (
    <div className="p-6 space-y-6 max-h-[90vh] overflow-y-auto">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wider">Orden de compra</p>
          <h2 className="text-xl font-bold text-gray-900 font-mono">{order.order_number}</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            {order.supplier ?? 'Sin proveedor asignado'} · Tienda {order.store_nbr} · {order.policy_used === 'manual' ? 'Creada a mano' : 'Generada por política (s,S)'}
          </p>
        </div>
        <button onClick={onClose} aria-label="Cerrar" className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-400">
          <X className="w-4 h-4" />
        </button>
      </div>

      {cancelled ? (
        <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          Orden cancelada. Sus productos pueden volver a generarse automáticamente.
        </div>
      ) : (
        <ol className="grid grid-cols-4 gap-2">
          {STEPS.map((s, i) => {
            const done = i <= stepIdx;
            return (
              <li key={s.status} className="flex flex-col items-center text-center gap-1.5">
                <div className={`w-full h-1.5 rounded-full ${done ? 'bg-orange-500' : 'bg-gray-100'}`} />
                <span className={`flex items-center gap-1 text-xs font-medium ${done ? 'text-gray-800' : 'text-gray-400'}`}>
                  {done && <Check className="w-3 h-3 text-orange-500" />}
                  {s.label}
                </span>
              </li>
            );
          })}
        </ol>
      )}

      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
        <div><dt className="text-xs text-gray-400">Emitida</dt><dd className="text-gray-800">{fmtDate(order.created_at)}</dd></div>
        <div><dt className="text-xs text-gray-400">Entrega esperada</dt><dd className="text-gray-800">{fmtDate(order.expected_delivery)}</dd></div>
        <div><dt className="text-xs text-gray-400">Recibida</dt><dd className="text-gray-800">{fmtDate(order.received_at)}</dd></div>
        <div><dt className="text-xs text-gray-400">Total</dt><dd className="text-gray-900 font-semibold">{order.total_cost != null ? fmtCLP(order.total_cost) : 'Faltan costos'}</dd></div>
      </dl>

      <div className="overflow-x-auto border border-gray-100 rounded-xl">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              {['Producto', 'Cantidad', 'Costo unit.', 'Subtotal', 'Stock al generar', 'Punto s'].map((h) => (
                <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {order.lines.map((l) => (
              <tr key={l.id}>
                <td className="px-4 py-2.5 font-medium text-gray-800">{l.family}</td>
                <td className="px-4 py-2.5 text-gray-700">{l.quantity.toLocaleString('es-CL')}</td>
                <td className="px-4 py-2.5 text-gray-600">{l.unit_cost != null ? fmtCLP(l.unit_cost) : '—'}</td>
                <td className="px-4 py-2.5 text-gray-700">{l.unit_cost != null ? fmtCLP(l.unit_cost * l.quantity) : '—'}</td>
                <td className="px-4 py-2.5 text-gray-500">{l.trigger_stock ?? '—'}</td>
                <td className="px-4 py-2.5 text-gray-500">{l.reorder_point_s ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {error && <p className="text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 pt-4">
        <div className="flex flex-wrap gap-2">
          <button onClick={pdf} disabled={downloading} className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 disabled:opacity-60">
            {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Descargar PDF
          </button>
          {order.status === 'pending' && (
            <button onClick={() => onEdit(order)} className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50">
              <Pencil className="w-4 h-4" /> Editar
            </button>
          )}
          {canCancel && (confirmCancel ? (
            <span className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">¿Cancelar la orden?</span>
              <button onClick={() => status.mutate('cancelled')} disabled={status.isPending} className="px-3 py-1.5 bg-red-600 text-white rounded-lg hover:opacity-90 disabled:opacity-60">
                Sí, cancelar
              </button>
              <button onClick={() => setConfirmCancel(false)} className="px-3 py-1.5 text-gray-500 hover:bg-gray-100 rounded-lg">No</button>
            </span>
          ) : (
            <button onClick={() => setConfirmCancel(true)} className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 rounded-lg hover:bg-red-50">
              <Ban className="w-4 h-4" /> Cancelar orden
            </button>
          ))}
        </div>
        {next && (
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400 hidden sm:inline">{next.hint}</span>
            <button
              onClick={() => status.mutate(next.status)}
              disabled={status.isPending}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 disabled:opacity-60"
            >
              {status.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              {next.label}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
