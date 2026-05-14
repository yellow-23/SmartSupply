import React from 'react';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface ModelMetric {
  name: string;
  mape: number;
  rmse: number;
  bias: number;
  status: 'best' | 'default';
}

const ModelComparisonTable: React.FC<{ models: ModelMetric[] }> = ({ models }) => {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-6 border-b border-gray-50 flex justify-between items-center">
        <h3 className="text-lg font-bold text-gray-800">Comparación de Modelos (AMS)</h3>
        <span className="px-3 py-1 bg-blue-50 text-unab-light text-xs font-bold rounded-full uppercase tracking-wider">
          SKU: GROCERY-001
        </span>
      </div>
      <table className="w-full text-left">
        <thead className="bg-gray-50/50">
          <tr>
            <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase">Modelo</th>
            <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase text-center">MAPE (%)</th>
            <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase text-center">RMSE</th>
            <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase text-center">BIAS</th>
            <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase text-center">Estado</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {models.map((m) => (
            <tr key={m.name} className={'hover:bg-gray-50/50 transition-colors ' + (m.status === 'best' ? 'bg-green-50/30' : '')}>
              <td className="px-6 py-4 font-bold text-gray-700">{m.name.toUpperCase()}</td>
              <td className="px-6 py-4 text-center text-gray-600">{m.mape.toFixed(2)}%</td>
              <td className="px-6 py-4 text-center text-gray-600">{m.rmse.toFixed(2)}</td>
              <td className="px-6 py-4 text-center text-gray-600">{m.bias > 0 ? '+' + m.bias.toFixed(2) : m.bias.toFixed(2)}</td>
              <td className="px-6 py-4 flex justify-center">
                {m.status === 'best' ? (
                  <div className="flex items-center space-x-1 text-green-600 bg-green-100 px-2 py-1 rounded-md">
                    <CheckCircle2 className="w-4 h-4" />
                    <span className="text-[10px] font-bold uppercase">Seleccionado</span>
                  </div>
                ) : (
                  <span className="text-gray-400 text-[10px] font-medium uppercase">Evaluado</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ModelComparisonTable;
