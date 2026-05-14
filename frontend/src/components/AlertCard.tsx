import React from 'react';
import { ShoppingCart } from 'lucide-react';

interface AlertCardProps {
  sku: string;
  stock: number;
  suggestedOrder: number;
}

const AlertCard: React.FC<AlertCardProps> = ({ sku, stock, suggestedOrder }) => {
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border-l-4 border-red-500 flex items-center justify-between">
      <div>
        <p className="text-[10px] font-bold text-red-500 uppercase tracking-widest mb-1">Stock Crítico</p>
        <h4 className="text-lg font-bold text-gray-800">{sku}</h4>
        <p className="text-sm text-gray-500 font-medium">Stock: {stock} unidades</p>
      </div>
      <button className="flex items-center space-x-2 px-4 py-2 bg-unab-light text-white rounded-xl text-sm font-bold shadow-lg shadow-blue-500/20 hover:bg-blue-700 transition-all">
        <ShoppingCart className="w-4 h-4" />
        <span>Ordenar {suggestedOrder}</span>
      </button>
    </div>
  );
};
export default AlertCard;
