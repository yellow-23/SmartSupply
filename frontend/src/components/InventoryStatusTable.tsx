import React from 'react';
import { Package, AlertCircle, ArrowRight } from 'lucide-react';

const InventoryStatusTable = ({ data }) => {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-6 border-b border-gray-50 flex justify-between items-center">
        <h3 className="text-lg font-bold text-gray-800">Estado de Inventario</h3>
        <span className="text-xs text-gray-500 font-medium">Actualizado hace 5 min</span>
      </div>
      <table className="w-full text-left text-sm">
        <thead className="bg-gray-50/50">
          <tr>
            <th className="px-6 py-4 font-bold text-gray-400 uppercase tracking-wider">SKU</th>
            <th className="px-6 py-4 font-bold text-gray-400 uppercase tracking-wider">Stock Actual</th>
            <th className="px-6 py-4 font-bold text-gray-400 uppercase tracking-wider">Punto Reorden (s)</th>
            <th className="px-6 py-4 font-bold text-gray-400 uppercase tracking-wider">Nivel Objetivo (S)</th>
            <th className="px-6 py-4 font-bold text-gray-400 uppercase tracking-wider">Estado</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {data.map((r, i) => (
            <tr key={i} className="hover:bg-gray-50/30">
              <td className="px-6 py-4 font-bold text-gray-700">{r.sku}</td>
              <td className="px-6 py-4 font-black text-gray-900">{r.stock}</td>
              <td className="px-6 py-4 text-gray-600">{r.s}</td>
              <td className="px-6 py-4 text-gray-600">{r.S}</td>
              <td className="px-6 py-4">
                {r.stock <= r.s ? (
                  <div className="flex items-center space-x-1 text-red-600 font-bold uppercase text-[10px]">
                    <AlertCircle className="w-3 h-3" />
                    <span>Crítico</span>
                  </div>
                ) : (
                  <span className="text-green-500 font-bold uppercase text-[10px]">Óptimo</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
export default InventoryStatusTable;
