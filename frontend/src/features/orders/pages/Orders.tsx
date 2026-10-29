import { useDeferredValue, useEffect, useState } from 'react';
import BrandLoader from "../../../shared/ui/BrandLoader";
import { keepPreviousData, useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ShoppingCart, CheckCircle, Clock, Truck, Plus, Loader2, XCircle, Download, Search, Wand2 } from 'lucide-react';
import { useActiveBusinessId, useActiveStoreNbr } from '../../auth/store/authStore';
import { fetchOrders, generateOrders, updateOrderStatus, exportOrders, PurchaseOrder } from '../api/orders';
import { downloadBlob } from '../../../shared/lib/utils';
import { toast } from '../../../shared/ui/toastStore';
import OrderDetail from '../components/OrderDetail';
import OrderForm from '../components/OrderForm';

const rowVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.015, duration: 0.12 } }),
};

const STATUS_LABELS: Record<PurchaseOrder['status'], string> = {
  pending: 'Pendiente',
  confirmed: 'Confirmada',
  in_transit: 'En tránsito',
  received: 'Recibida',
  cancelled: 'Cancelada',
};

const STATUS_STYLES: Record<PurchaseOrder['status'], string> = {
  pending: 'bg-amber-100 text-amber-700 border border-amber-200',
  confirmed: 'bg-green-100 text-green-700 border border-green-200',
  in_transit: 'bg-blue-100 text-blue-700 border border-blue-200',
  received: 'bg-gray-100 text-gray-600 border border-gray-200',
  cancelled: 'bg-red-100 text-red-500 border border-red-200',
};

const NEXT_STATUS: Partial<Record<PurchaseOrder['status'], { status: PurchaseOrder['status']; label: string }>> = {
  pending: { status: 'confirmed', label: 'Confirmar' },
  confirmed: { status: 'in_transit', label: 'Marcar en tránsito' },
  in_transit: { status: 'received', label: 'Marcar recibida' },
};

const STATUS_FILTER_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'Todas' },
  { value: 'pending', label: 'Pendientes' },
  { value: 'confirmed', label: 'Confirmadas' },
  { value: 'in_transit', label: 'En tránsito' },
  { value: 'received', label: 'Recibidas' },
  { value: 'cancelled', label: 'Canceladas' },
];

const fmtCLP = (n: number) => `$${Math.round(n).toLocaleString('es-CL')}`;

const fmtDate = (s: string | null) =>
  s ? new Date(s).toLocaleDateString('es-CL', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';

export default function Orders() {
  const businessId = useActiveBusinessId();
  const queryClient = useQueryClient();

  const storeNbr = useActiveStoreNbr();
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [selected, setSelected] = useState<PurchaseOrder | null>(null);
  const [form, setForm] = useState<{ order: PurchaseOrder | null } | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const deferredSearch = useDeferredValue(search);
  const filters = { store_nbr: String(storeNbr), status: statusFilter, q: deferredSearch.trim(), date_from: dateFrom, date_to: dateTo };

  const ordersQuery = useQuery({
    queryKey: ['orders', businessId, filters],
    queryFn: () => fetchOrders(businessId!, filters),
    enabled: businessId != null,
    placeholderData: keepPreviousData, // al buscar/filtrar no se vuelve al cargador
  });

  const statusMutation = useMutation({
    mutationFn: ({ orderId, newStatus }: { orderId: number; newStatus: string }) =>
      updateOrderStatus(orderId, businessId!, newStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders', businessId] });
      queryClient.invalidateQueries({ predicate: (q) => String(q.queryKey[0]).startsWith('inventory') });
      toast.success('Estado actualizado');
    },
  });

  const generateMutation = useMutation({
    mutationFn: () => generateOrders(businessId!, storeNbr),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['orders', businessId] });
      toast.success(
        data.length > 0
          ? `Se generaron ${data.length} OC: ${data.map((o) => `${o.order_number} (${o.supplier ?? 'sin proveedor'})`).join(', ')}`
          : 'No hay productos críticos sin orden abierta.'
      );
    },
  });

  const handleExport = async () => {
    if (!businessId) return;
    setIsExporting(true);
    try {
      const blob = await exportOrders(businessId, filters);
      downloadBlob(blob, `ordenes_${businessId}.xlsx`);
    } finally {
      setIsExporting(false);
    }
  };

  const orders = ordersQuery.data ?? [];

  // ?oc=ID (desde Inventario) abre el detalle de esa orden una vez cargada la lista
  useEffect(() => {
    const id = Number(new URLSearchParams(window.location.search).get('oc'));
    const found = id ? orders.find((o) => o.id === id) : undefined;
    if (found) {
      setSelected(found);
      window.history.replaceState(null, '', '/orders');
    }
  }, [ordersQuery.data]);

  const countByStatus = (s: PurchaseOrder['status']) => orders.filter((o) => o.status === s).length;

  const today = new Date().toISOString().slice(0, 10);
  const receivedToday = orders.filter(
    (o) => o.status === 'received' && o.received_at?.slice(0, 10) === today
  ).length;

  if (!businessId) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        Selecciona un negocio para ver las órdenes.
      </div>
    );
  }

  if (ordersQuery.isLoading) {
    return <BrandLoader label="Cargando tus órdenes de compra..." className="min-h-[60vh]" />;
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: 'Pendientes', value: countByStatus('pending'), icon: Clock, bg: 'bg-amber-50', text: 'text-amber-500' },
          { label: 'Confirmadas', value: countByStatus('confirmed'), icon: CheckCircle, bg: 'bg-emerald-50', text: 'text-emerald-500' },
          { label: 'En tránsito', value: countByStatus('in_transit'), icon: Truck, bg: 'bg-blue-50', text: 'text-blue-700' },
          { label: 'Recibidas hoy', value: receivedToday, icon: ShoppingCart, bg: 'bg-orange-50', text: 'text-orange-600' },
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
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50 flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-gray-700">Órdenes de compra</span>
            {ordersQuery.isLoading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <div className="relative">
              <Search className="w-4 h-4 text-gray-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="N° OC, producto o proveedor"
                aria-label="Buscar órdenes"
                className="border border-gray-200 rounded-lg pl-8 pr-3 py-1.5 text-sm text-gray-600 w-56"
              />
            </div>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              aria-label="Creada desde"
              className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm text-gray-600"
            />
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              aria-label="Creada hasta"
              className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm text-gray-600"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-600"
            >
              {STATUS_FILTER_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors active:scale-[0.97] disabled:opacity-60"
            >
              {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              Exportar Excel
            </button>
            <button
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              title="Crea una OC por proveedor con los productos bajo su punto de reorden (s)"
              className="flex items-center gap-2 px-3 py-2 text-sm border border-orange-200 text-orange-700 bg-orange-50 rounded-lg hover:bg-orange-100 transition-transform active:scale-[0.97] disabled:opacity-60"
            >
              {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />}
              Generar automáticas
            </button>
            <button
              onClick={() => setForm({ order: null })}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90 transition-transform active:scale-[0.97]"
            >
              <Plus className="w-4 h-4" />
              Nueva orden
            </button>
          </div>
        </div>

        {ordersQuery.isError && (
          <div className="flex items-center gap-2 px-6 py-4 text-sm text-red-500">
            <XCircle className="w-4 h-4" />
            Error al cargar órdenes.
          </div>
        )}

        {!ordersQuery.isLoading && !ordersQuery.isError && orders.length === 0 && (
          <div className="px-6 py-10 text-center text-sm text-gray-400">
            No hay órdenes con el filtro seleccionado.
          </div>
        )}

        {orders.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {['N° OC', 'Proveedor', 'Productos', 'Total', 'Estado', 'Creada', 'Entrega esperada', ''].map((h, hi) => (
                    <th key={hi} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {orders.map((o, i) => {
                  const next = NEXT_STATUS[o.status];
                  return (
                    <motion.tr
                      key={o.id}
                      custom={i}
                      initial="hidden"
                      animate="visible"
                      variants={rowVariants}
                      onClick={() => setSelected(o)}
                      className="hover:bg-gray-50 transition-colors cursor-pointer"
                    >
                      <td className="px-4 py-4 font-mono font-medium text-gray-800 whitespace-nowrap">{o.order_number}</td>
                      <td className="px-4 py-4 text-gray-700 whitespace-nowrap">{o.supplier ?? <span className="text-gray-400">Sin proveedor</span>}</td>
                      <td className="px-4 py-4 text-gray-500 max-w-[260px] truncate" title={o.lines.map((l) => l.family).join(', ')}>
                        {o.lines.length} · {o.lines.map((l) => l.family).join(', ')}
                      </td>
                      <td className="px-4 py-4 text-gray-700 whitespace-nowrap">{o.total_cost != null ? fmtCLP(o.total_cost) : '—'}</td>
                      <td className="px-4 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[o.status]}`}>
                          {STATUS_LABELS[o.status]}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-gray-400 text-xs whitespace-nowrap">{fmtDate(o.created_at)}</td>
                      <td className="px-4 py-4 text-gray-400 text-xs whitespace-nowrap">{fmtDate(o.expected_delivery)}</td>
                      <td className="px-4 py-4">
                        {next && (
                          <button
                            onClick={(e) => { e.stopPropagation(); statusMutation.mutate({ orderId: o.id, newStatus: next.status }); }}
                            disabled={statusMutation.isPending}
                            className="px-3 py-1 text-xs bg-orange-50 text-orange-700 border border-orange-200 rounded-lg hover:bg-orange-100 transition-colors active:scale-[0.95] disabled:opacity-50 whitespace-nowrap"
                          >
                            {next.label}
                          </button>
                        )}
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <OrderDetail
        order={selected}
        businessId={businessId}
        onClose={() => setSelected(null)}
        onEdit={(o) => setForm({ order: o })}
        onChanged={(o) => {
          setSelected(o);
          queryClient.invalidateQueries({ queryKey: ['orders', businessId] });
          queryClient.invalidateQueries({ predicate: (q) => String(q.queryKey[0]).startsWith('inventory') });
        }}
      />
      <OrderForm
        open={!!form}
        businessId={businessId}
        storeNbr={storeNbr}
        order={form?.order}
        onClose={() => setForm(null)}
        onSaved={(o) => {
          toast.success(form?.order ? `${o.order_number} actualizada` : `${o.order_number} creada`);
          setForm(null);
          setSelected(o);
          queryClient.invalidateQueries({ queryKey: ['orders', businessId] });
        }}
      />
    </div>
  );
}
