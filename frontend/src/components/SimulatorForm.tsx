import React from 'react';
import { Play } from 'lucide-react';

const SimulatorForm = () => {
  return (
    <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
      <h3 className="text-xl font-bold text-gray-800 mb-6">Simulador de Políticas</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="space-y-2">
          <label className="text-xs font-bold text-gray-400 uppercase">Costo de Pedido (K)</label>
          <input type="number" className="w-full p-3 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-unab-light transition-all font-bold" defaultValue={5000} />
        </div>
        <div className="space-y-2">
          <label className="text-xs font-bold text-gray-400 uppercase">Costo Mantención (h)</label>
          <input type="number" className="w-full p-3 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-unab-light transition-all font-bold" defaultValue={150} />
        </div>
        <div className="space-y-2">
          <label className="text-xs font-bold text-gray-400 uppercase">Lead Time (días)</label>
          <input type="number" className="w-full p-3 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-unab-light transition-all font-bold" defaultValue={3} />
        </div>
        <div className="space-y-2">
          <label className="text-xs font-bold text-gray-400 uppercase">Nivel Servicio (%)</label>
          <input type="number" className="w-full p-3 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-unab-light transition-all font-bold" defaultValue={95} />
        </div>
      </div>
      <button className="w-full flex items-center justify-center space-x-3 py-4 bg-unab-blue text-white rounded-2xl font-bold shadow-xl shadow-blue-900/20 hover:bg-black transition-all">
        <Play className="w-5 h-5 fill-current" />
        <span>Correr Simulación Walk-forward</span>
      </button>
    </div>
  );
};
export default SimulatorForm;
