import React from 'react'; import { Download } from 'lucide-react';
const HistoryTable = ({ data }) => {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-6 border-b border-gray-50 flex justify-between items-center">
        <h3 className="text-lg font-bold text-gray-800">Historial de Ventas</h3>
        <button className="px-3 py-1 bg-gray-50 border border-gray-200 rounded text-xs font-bold transition-all">CSV</button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50/50">
            <tr>
              <th className="px-6 py-4 font-bold text-gray-400">Fecha</th>
              <th className="px-6 py-4 font-bold text-gray-400">SKU</th>
              <th className="px-6 py-4 font-bold text-gray-400">Ventas</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r, i) => (
              <tr key={i} className="border-t border-gray-50 hover:bg-gray-50/50">
                <td className="px-6 py-4">{r.date}</td>
                <td className="px-6 py-4 font-bold text-gray-700">{r.sku}</td>
                <td className="px-6 py-4">{r.sales}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
export default HistoryTable;
