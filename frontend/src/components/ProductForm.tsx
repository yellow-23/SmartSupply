import React from 'react';
import { Save, X } from 'lucide-react';

const ProductForm = () => {
  return (
    <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h3 className="text-xl font-bold text-gray-800">Registrar Nuevo Producto</h3>
        <button aria-label="Cerrar" className="p-2 hover:bg-gray-100 rounded-full"><X className="w-5 h-5 text-gray-400" /></button>
      </div>
      <form className="space-y-6">
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-2">
            <label htmlFor="sku" className="text-xs font-bold text-gray-400 uppercase">SKU ID</label>
            <input id="sku" type="text" className="w-full p-3 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-blue-900 transition-all font-medium" placeholder="BEV-001" />
          </div>
          <div className="space-y-2">
            <label htmlFor="nombre" className="text-xs font-bold text-gray-400 uppercase">Nombre</label>
            <input id="nombre" type="text" className="w-full p-3 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-blue-900 transition-all font-medium" placeholder="Agua Mineral 500ml" />
          </div>
        </div>
        <div className="space-y-2">
          <label htmlFor="familia" className="text-xs font-bold text-gray-400 uppercase">Familia</label>
          <select id="familia" className="w-full p-3 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-blue-900 transition-all font-medium">
            <option>BEVERAGES</option>
            <option>GROCERY I</option>
            <option>CLEANING</option>
          </select>
        </div>
        <div className="grid grid-cols-3 gap-6">
          <div className="space-y-2">
            <label htmlFor="costo" className="text-xs font-bold text-gray-400 uppercase">Costo Unitario</label>
            <input id="costo" type="number" className="w-full p-3 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-blue-900 transition-all font-medium" defaultValue={0} />
          </div>
          <div className="space-y-2">
            <label htmlFor="leadtime" className="text-xs font-bold text-gray-400 uppercase">Lead Time</label>
            <input id="leadtime" type="number" className="w-full p-3 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-blue-900 transition-all font-medium" defaultValue={1} />
          </div>
          <div className="space-y-2">
            <label htmlFor="moq" className="text-xs font-bold text-gray-400 uppercase">MOQ</label>
            <input id="moq" type="number" className="w-full p-3 bg-gray-50 border-none rounded-xl focus:ring-2 focus:ring-blue-900 transition-all font-medium" defaultValue={1} />
          </div>
        </div>
        <button className="w-full flex items-center justify-center space-x-2 py-4 bg-orange-600 text-white rounded-2xl font-bold hover:opacity-90 transition-all mt-4">
          <Save className="w-5 h-5" />
          <span>Guardar Producto</span>
        </button>
      </form>
    </div>
  );
};
export default ProductForm;
