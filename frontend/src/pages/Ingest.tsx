import React, { useState } from 'react';
import { Upload, FileText, ImageIcon, CheckCircle, AlertCircle, Loader2, Send } from 'lucide-react';

const Ingest = () => {
  const [step, setStep] = useState(1); // 1: Upload, 2: Preview, 3: Success
  const [isProcessing, setIsProcessing] = useState(false);

  const handleUpload = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      setStep(2);
    }, 2000);
  };

  const handleConfirm = () => {
    setStep(3);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Ingesta Inteligente</h2>
        <p className="text-sm text-gray-500">Usa IA (Claude) para extraer ventas desde fotos, PDF o Excel</p>
      </div>

      {step === 1 && (
        <div className="bg-white p-12 rounded-3xl border-2 border-dashed border-gray-200 flex flex-col items-center justify-center text-center space-y-6 hover:border-unab-light transition-colors group cursor-pointer" onClick={handleUpload}>
          {isProcessing ? (
            <div className="space-y-4">
              <Loader2 className="w-16 h-16 text-unab-light animate-spin mx-auto" />
              <p className="text-lg font-bold text-gray-700">Claude está analizando tu archivo...</p>
              <p className="text-sm text-gray-400">Identificando columnas de fecha, familia y ventas</p>
            </div>
          ) : (
            <>
              <div className="w-20 h-20 bg-blue-50 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                <Upload className="w-10 h-10 text-unab-light" />
              </div>
              <div className="space-y-2">
                <p className="text-xl font-bold text-gray-800">Sube tu archivo de ventas</p>
                <p className="text-gray-400 text-sm max-w-sm">Aceptamos fotos de cuadernos, planillas Excel desordenadas o reportes PDF</p>
              </div>
              <div className="flex space-x-4">
                <div className="flex items-center space-x-1 text-[10px] font-bold text-gray-400 uppercase tracking-tighter">
                  <ImageIcon className="w-3 h-3" /> <span>JPG/PNG</span>
                </div>
                <div className="flex items-center space-x-1 text-[10px] font-bold text-gray-400 uppercase tracking-tighter">
                  <FileText className="w-3 h-3" /> <span>PDF/XLSX</span>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {step === 2 && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-500" />
              </div>
              <div>
                <h4 className="font-bold text-gray-800">Extracción Exitosa</h4>
                <p className="text-xs text-gray-500">Se encontraron 42 registros entre 2025-04-01 y 2025-05-10</p>
              </div>
            </div>
            <button 
              onClick={handleConfirm}
              className="flex items-center space-x-2 px-6 py-2.5 bg-unab-light text-white rounded-xl font-bold shadow-lg shadow-blue-500/20 hover:bg-blue-700 transition-all"
            >
              <Send className="w-4 h-4" />
              <span>Confirmar Carga</span>
            </button>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 font-bold text-gray-400 uppercase">Fecha</th>
                  <th className="px-6 py-3 font-bold text-gray-400 uppercase">Familia</th>
                  <th className="px-6 py-3 font-bold text-gray-400 uppercase">Ventas</th>
                  <th className="px-6 py-3 font-bold text-gray-400 uppercase">Ajuste IA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {[1,2,3,4,5].map(i => (
                  <tr key={i}>
                    <td className="px-6 py-4 font-medium">2025-05-0{i}</td>
                    <td className="px-6 py-4 font-bold">ABARROTES</td>
                    <td className="px-6 py-4 font-black">{(120 * i).toLocaleString()}</td>
                    <td className="px-6 py-4">
                      <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded font-bold uppercase tracking-tighter">Normalizado</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="bg-white p-12 rounded-3xl shadow-sm border border-gray-100 text-center space-y-6 animate-in zoom-in duration-500">
          <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto shadow-xl shadow-green-500/20">
            <CheckCircle className="w-10 h-10 text-white" />
          </div>
          <div className="space-y-2">
            <h3 className="text-2xl font-bold text-gray-800">¡Datos Cargados!</h3>
            <p className="text-gray-500 max-w-sm mx-auto">Los registros ya están disponibles para los modelos de forecasting y políticas de inventario.</p>
          </div>
          <button 
            onClick={() => setStep(1)}
            className="px-8 py-3 bg-gray-900 text-white rounded-xl font-bold hover:bg-black transition-all"
          >
            Subir otro archivo
          </button>
        </div>
      )}
    </div>
  );
};
export default Ingest;
