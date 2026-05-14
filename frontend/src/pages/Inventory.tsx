import React from 'react';
import { Package, TrendingDown, ClipboardList } from 'lucide-react';
import InventoryStatusTable from '../components/InventoryStatusTable';
import AlertCard from '../components/AlertCard';

const Inventory = () => {
  const mockAlerts = [
    { sku: 'GROCERY-001', stock: 12, suggestedOrder: 88 },
    { sku: 'BEVERAGES-005', stock: 5, suggestedOrder: 45 },
  ];

  const mockInventory = [
    { sku: 'GROCERY-001', stock: 12, s: 30, S: 100 },
    { sku: 'GROCERY-002', stock: 85, s: 40, S: 120 },
    { sku: 'BEVERAGES-001', stock: 42, s: 20, S: 80 },
    { sku: 'BEVERAGES-005', stock: 5, s: 15, S: 50 },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Gestión de Inventario</h2>
        <p className="text-sm text-gray-500">Política de reabastecimiento (s, S) y EOQ</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {mockAlerts.map((alert, i) => (
          <AlertCard key={i} {...alert} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <InventoryStatusTable data={mockInventory} />
        </div>
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center space-x-2">
              <ClipboardList className="w-5 h-5 text-unab-light" />
              <span>Resumen de Órdenes</span>
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-500 font-medium">Pendientes</span>
                <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 font-black rounded-full">5</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-500 font-medium">En Tránsito</span>
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 font-black rounded-full">2</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-500 font-medium">Recibidas (Hoy)</span>
                <span className="px-2 py-0.5 bg-green-100 text-green-700 font-black rounded-full">3</span>
              </div>
            </div>
          </div>
          <button className="w-full flex items-center justify-center space-x-2 p-4 bg-gray-900 text-white rounded-2xl font-bold hover:bg-black transition-all shadow-xl shadow-black/10">
            <Package className="w-5 h-5" />
            <span>Generar Todas las Órdenes</span>
          </button>
        </div>
      </div>
    </div>
  );
};
export default Inventory;
