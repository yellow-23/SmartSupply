import React, { useState } from 'react';
import BrandLoader from "../../../shared/ui/BrandLoader";
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Package, AlertCircle, TrendingDown, RefreshCw, Loader2, Download, ShoppingCart } from 'lucide-react';
import { toast } from '../../../shared/ui/toastStore';
import { useActiveBusinessId, useActiveStoreNbr } from '../../auth/store/authStore';
import {
  fetchAlerts,
  fetchInventoryStatus,
  fetchInventoryMetrics,
  exportAlerts,
  InventoryAlert,
} from '../api/inventory';
import { fetchOrders, generateOrders } from '../../orders/api/orders';
import OrderForm from '../../orders/components/OrderForm';
import { useNavigate } from 'react-router-dom';
import { fetchProducts } from '../../products/api/products';
import { downloadBlob } from '../../../shared/lib/utils';

const urgencyBadge = (urgency: InventoryAlert['urgency']) => {
  if (urgency === 'critical') return 'bg-red-100 text-red-700 border border-red-200';
  if (urgency === 'high') return 'bg-orange-100 text-orange-700 border border-orange-200';
  return 'bg-gray-100 text-gray-500 border border-gray-200';
};

const urgencyLabel: Record<InventoryAlert['urgency'], string> = {
  critical: 'Crítico',
  high: 'Alto',
  normal: 'Normal',
};

const fmtCLP = (n: number) =>
  n.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 });

export default function Inventory() {
  const businessId = useActiveBusinessId();
  const queryClient = useQueryClient();

  const storeNbr = useActiveStoreNbr();
  // ?producto=X (desde el panel de alertas del Dashboard) abre ese producto directo
  const [selectedFamily, setSelectedFamily] = useState<string | null>(() => new URLSearchParams(window.location.search).get('producto'));
  const [isExporting, setIsExporting] = useState(false);
  const [orderFormOpen, setOrderFormOpen] = useState(false);
  const navigate = useNavigate();

  // OC abierta (no recibida ni cancelada) que ya incluye el producto seleccionado: evita pedirlo dos veces
  const openOrderQuery = useQuery({
    queryKey: ['orders', businessId, 'open-for', storeNbr, selectedFamily],
    queryFn: () => fetchOrders(businessId!, { store_nbr: String(storeNbr), q: selectedFamily! }),
    enabled: businessId != null && !!selectedFamily,
    select: (orders) => orders.find((o) =>
      ['pending', 'confirmed', 'in_transit'].includes(o.status) && o.lines.some((l) => l.family === selectedFamily)),
  });

  const alertsQuery = useQuery({
    queryKey: ['inventory-alerts', businessId, storeNbr],
    queryFn: () => fetchAlerts(businessId!, storeNbr),
    enabled: businessId != null,
  });

  const familiesQuery = useQuery({
    queryKey: ['inventory-families', businessId, storeNbr],
    queryFn: () => fetchProducts({ business_id: businessId!, store_nbr: storeNbr, limit: 100 }),
    enabled: businessId != null,
  });

  const statusQuery = useQuery({
    queryKey: ['inventory-status', selectedFamily, businessId, storeNbr],
    queryFn: () => fetchInventoryStatus(selectedFamily!, businessId!, storeNbr),
    enabled: selectedFamily != null && businessId != null,
  });

  const metricsQuery = useQuery({
    queryKey: ['inventory-metrics', selectedFamily, businessId, storeNbr],
    queryFn: () => fetchInventoryMetrics(selectedFamily!, businessId!, storeNbr),
    enabled: selectedFamily != null && businessId != null,
  });

  const generateMutation = useMutation({
    mutationFn: () => generateOrders(businessId!, storeNbr),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['orders', businessId] });
      toast.success(
        data.length > 0
          ? `Se generaron ${data.length} orden${data.length !== 1 ? 'es' : ''} automática${data.length !== 1 ? 's' : ''}.`
          : 'No hay SKUs que requieran una orden por ahora.'
      );
    },
  });

  const handleExport = async () => {
    if (!businessId) return;
    setIsExporting(true);
    try {
      const blob = await exportAlerts(businessId, storeNbr);
      downloadBlob(blob, `alertas_inventario_${businessId}.xlsx`);
    } finally {
      setIsExporting(false);
    }
  };

  const alerts = alertsQuery.data?.alerts ?? [];
  const hasCLPSkus = alertsQuery.data?.has_clp_skus ?? false;
  const allFamilies = Array.from(
    new Set([...(familiesQuery.data?.items.map((p) => p.family) ?? []), ...alerts.map((a) => a.family)])
  ).sort();

  const selectedProduct = familiesQuery.data?.items.find((p) => p.family === selectedFamily);
  const suggestedQty = statusQuery.data
    ? Math.max(Math.ceil(statusQuery.data.order_up_to_S - statusQuery.data.current_stock), Number(selectedProduct?.moq ?? 0), 1)
    : 1;

  if (!businessId) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        Selecciona un negocio para ver el inventario.
      </div>
    );
  }

  if (alertsQuery.isLoading) {
    return (
      <BrandLoader
        label="Calculando tu inventario..."
        hint="Revisamos la demanda de cada producto para saber cuándo y cuánto pedir."
        className="min-h-[60vh]"
      />
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Gestión de Inventario</h2>
          <p className="text-sm text-gray-500">Cuándo y cuánto pedir para mantener el stock óptimo</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-xs text-gray-500 font-medium">Tienda</label>
          <input
            type="number"
            min={1}
            value={storeNbr}
            onChange={(e) => setStoreNbr(Number(e.target.value))}
            className="w-20 border border-gray-200 rounded-lg px-2 py-1.5 text-sm text-gray-700"
          />
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-60"
          >
            {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Exportar Excel
          </button>
        </div>
      </div>

      {hasCLPSkus && (
        <div className="flex items-start gap-3 px-5 py-4 bg-amber-50 border border-amber-200 rounded-2xl text-amber-800">
          <AlertCircle className="w-5 h-5 mt-0.5 shrink-0" />
          <div className="text-sm">
            <p className="font-semibold">Algunos SKUs tienen ventas en pesos (CLP)</p>
            <p className="text-amber-700">
              El cálculo de EOQ y punto de reorden requiere precio unitario. Estos SKUs no generarán
              sugerencias de compra hasta que se configure su precio.
            </p>
          </div>
        </div>
      )}

      {/* Alerts */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            Alertas de reabastecimiento
          </h3>
          {alertsQuery.isLoading && <Loader2 className="w-4 h-4 animate-spin text-gray-400" />}
        </div>
        {alertsQuery.isError && (
          <p className="text-sm text-red-500">Error al cargar alertas.</p>
        )}
        {!alertsQuery.isLoading && alerts.length === 0 && !alertsQuery.isError && (
          <p className="text-sm text-gray-400">Sin alertas activas.</p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {alerts.map((a, i) => (
            <motion.button
              key={a.family}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.02, duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
              onClick={() => setSelectedFamily(a.family)}
              className={`text-left bg-white rounded-2xl shadow-sm border p-5 hover:shadow-md transition-all active:scale-[0.98] ${
                selectedFamily === a.family ? 'border-orange-400' : 'border-gray-100'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <span className="text-sm font-semibold text-gray-800 truncate pr-2">{a.family}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${urgencyBadge(a.urgency)}`}>
                  {urgencyLabel[a.urgency]}
                </span>
              </div>
              {a.needs_cost_setup ? (
                <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-1.5">
                  Falta configurar el costo unitario para calcular cuánto pedir
                </p>
              ) : (
                <div className="grid grid-cols-3 gap-2 text-xs text-gray-500">
                  <div>
                    <p className="font-medium text-gray-800 text-base">{a.current_stock}</p>
                    <p>Stock actual</p>
                  </div>
                  <div>
                    <p className="font-medium text-gray-800 text-base">{a.reorder_point_s}</p>
                    <p>Punto s</p>
                  </div>
                  <div>
                    <p className="font-medium text-orange-600 text-base">{a.order_quantity}</p>
                    <p>A pedir</p>
                  </div>
                </div>
              )}
            </motion.button>
          ))}
        </div>
      </div>

      {/* Family selector + detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center gap-3">
            <label className="text-xs text-gray-500 font-medium whitespace-nowrap">Familia SKU</label>
            <select
              value={selectedFamily ?? ''}
              onChange={(e) => setSelectedFamily(e.target.value || null)}
              className="flex-1 border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700"
            >
              <option value="">-- Selecciona una familia --</option>
              {allFamilies.map((family) => (
                <option key={family} value={family}>{family}</option>
              ))}
            </select>
          </div>

          {selectedFamily && (
            <>
              {(statusQuery.isLoading || metricsQuery.isLoading) && (
                <div className="flex items-center gap-2 text-sm text-gray-400 py-8">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Cargando datos de inventario...
                </div>
              )}
              {(statusQuery.isError || metricsQuery.isError) && (
                <p className="text-sm text-red-500">Error al cargar detalles del SKU.</p>
              )}

              {statusQuery.data && (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-4">
                    Estado de inventario — {selectedFamily}
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { label: 'Stock actual', value: statusQuery.data.current_stock, highlight: statusQuery.data.needs_reorder },
                      { label: 'Punto reorden (s)', value: statusQuery.data.reorder_point_s },
                      { label: 'Nivel máximo (S)', value: statusQuery.data.order_up_to_S },
                      { label: 'EOQ calculado', value: statusQuery.data.eoq },
                    ].map(({ label, value, highlight }) => (
                      <div key={label} className={`rounded-xl p-4 ${highlight ? 'bg-red-50' : 'bg-gray-50'}`}>
                        <p className={`text-xl font-bold ${highlight ? 'text-red-600' : 'text-gray-800'}`}>{Math.round(value).toLocaleString('es-CL')}</p>
                        <p className="text-xs text-gray-500 mt-1">{label}</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3 text-xs">
                    <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full">
                      Política: {statusQuery.data.policy}
                    </span>
                    {statusQuery.data.days_until_stockout != null && (
                      <span className={`px-3 py-1 rounded-full font-medium ${
                        statusQuery.data.days_until_stockout <= 7
                          ? 'bg-red-100 text-red-700'
                          : 'bg-amber-100 text-amber-700'
                      }`}>
                        Quiebre en {statusQuery.data.days_until_stockout} días
                      </span>
                    )}
                    {statusQuery.data.needs_reorder && (
                      <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full font-medium">
                        Requiere reposición
                      </span>
                    )}
                  </div>
                  <div className="mt-5 pt-4 border-t border-gray-100 flex flex-wrap items-center justify-between gap-3">
                    {openOrderQuery.data ? (
                      <p className="text-sm text-gray-600">
                        Ya hay una orden abierta con este producto:{' '}
                        <button
                          onClick={() => navigate(`/orders?oc=${openOrderQuery.data!.id}`)}
                          className="font-semibold text-orange-600 hover:underline"
                        >
                          {openOrderQuery.data.order_number}
                        </button>
                      </p>
                    ) : (
                      <p className="text-sm text-gray-500">
                        Cantidad sugerida: <span className="font-semibold text-gray-800">{suggestedQty.toLocaleString('es-CL')} uds</span>
                        <span className="text-gray-400"> (hasta el nivel máximo S{selectedProduct?.moq ? `, mínimo ${selectedProduct.moq}` : ''})</span>
                      </p>
                    )}
                    {!openOrderQuery.data && (
                      <button
                        onClick={() => setOrderFormOpen(true)}
                        className="flex items-center gap-2 px-4 py-2 text-sm bg-orange-600 text-white rounded-lg hover:opacity-90"
                      >
                        <ShoppingCart className="w-4 h-4" />
                        Crear orden de compra
                      </button>
                    )}
                  </div>
                </div>
              )}

              {metricsQuery.data && (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                  <h4 className="text-sm font-semibold text-gray-700 mb-4">
                    Métricas últimos 30 días
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="rounded-xl p-4 bg-gray-50">
                      <p className="text-lg font-bold text-gray-800">
                        {fmtCLP(metricsQuery.data.capital_inmovilizado)}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">Capital inmovilizado</p>
                    </div>
                    <div className="rounded-xl p-4 bg-gray-50">
                      <p className="text-lg font-bold text-gray-800">
                        {metricsQuery.data.stockout_rate.toFixed(1)}%
                      </p>
                      <p className="text-xs text-gray-500 mt-1">Tasa de quiebre</p>
                    </div>
                    <div className="rounded-xl p-4 bg-gray-50">
                      <p className="text-lg font-bold text-gray-800">
                        {metricsQuery.data.service_level.toFixed(1)}%
                      </p>
                      <p className="text-xs text-gray-500 mt-1">Nivel de servicio</p>
                    </div>
                    <div className="rounded-xl p-4 bg-gray-50">
                      <p className="text-lg font-bold text-gray-800">
                        {metricsQuery.data.inventory_turnover.toFixed(2)}x
                      </p>
                      <p className="text-xs text-gray-500 mt-1">Rotación</p>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-orange-500" />
              Resumen de alertas
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-gray-500">Críticas</span>
                <span className="px-2 py-0.5 bg-red-100 text-red-700 font-bold rounded-full text-xs">
                  {alerts.filter((a) => a.urgency === 'critical').length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-500">Altas</span>
                <span className="px-2 py-0.5 bg-orange-100 text-orange-700 font-bold rounded-full text-xs">
                  {alerts.filter((a) => a.urgency === 'high').length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-500">Total</span>
                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 font-bold rounded-full text-xs">
                  {alertsQuery.data?.count ?? 0}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="w-full flex items-center justify-center gap-2 p-4 bg-orange-600 text-white rounded-2xl font-bold hover:opacity-90 transition-all active:scale-[0.98] disabled:opacity-60"
          >
            {generateMutation.isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Package className="w-5 h-5" />
            )}
            <span>Generar Órdenes Automáticas</span>
          </button>

          {generateMutation.isError && (
            <p className="text-xs text-red-500 text-center">
              Error al generar órdenes. Intenta nuevamente.
            </p>
          )}
        </div>
      </div>
      {businessId != null && selectedFamily && (
        <OrderForm
          open={orderFormOpen}
          businessId={businessId}
          storeNbr={storeNbr}
          draft={{
            supplier: selectedProduct?.supplier ?? null,
            lines: [{ family: selectedFamily, quantity: suggestedQty, unit_cost: selectedProduct?.unit_cost ?? null }],
          }}
          onClose={() => setOrderFormOpen(false)}
          onSaved={(o) => {
            setOrderFormOpen(false);
            queryClient.invalidateQueries({ queryKey: ['orders', businessId] });
            toast.success(`${o.order_number} creada`);
            navigate(`/orders?oc=${o.id}`);
          }}
        />
      )}
    </div>
  );
}
