import { useEffect, useRef, useState } from "react";
import { Upload, FileText, ImageIcon, CheckCircle, AlertTriangle, Loader2, Send, X, Bot } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { useAuthStore } from "../store/authStore";
import { previewIngest, confirmIngest, chatIngest, IngestPreview, ChatMessage, ChatResponse } from "../api/ingest";

const ACCEPTED = ".jpg,.jpeg,.png,.webp,.pdf,.xlsx,.xls,.csv";

export default function Ingest() {
  const user = useAuthStore(s => s.user);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [storeNbr, setStoreNbr] = useState(1);
  const [preview, setPreview] = useState<IngestPreview | null>(null);
  const [fileName, setFileName] = useState("");
  const [step, setStep] = useState<"upload" | "preview" | "success">("upload");
  const [successData, setSuccessData] = useState<{ loaded: number; families: string[]; start: string; end: string } | null>(null);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const previewMut = useMutation({
    mutationFn: (file: File) => previewIngest(file),
    onSuccess: (data) => {
      setPreview(data);
      setStep("preview");
      setChatMessages([]);
    },
  });

  const chatMut = useMutation({
    mutationFn: ({ messages, summary }: { messages: ChatMessage[]; summary: string }) =>
      chatIngest(messages, summary),
    onSuccess: (res: ChatResponse, { messages }) => {
      setChatMessages([...messages, { role: "assistant", content: res.reply }]);
      if (res.trigger_confirm && preview) {
        confirmMut.mutate();
      }
    },
  });

  function buildPreviewSummary(p: IngestPreview): string {
    return `Archivo procesado: ${p.store_name}. ${p.records_found} registros extraídos. Rango: ${p.date_range_start} a ${p.date_range_end}. Familias detectadas: ${p.families_detected.join(", ")}. Advertencias: ${p.warnings.length > 0 ? p.warnings.join(" | ") : "ninguna"}.`;
  }

  useEffect(() => {
    if (step === "preview" && preview && chatMessages.length === 0) {
      const summary = buildPreviewSummary(preview);
      const firstMsg: ChatMessage = {
        role: "user",
        content: `Extracción completada. ${preview.records_found} registros, familias: ${preview.families_detected.join(", ")}, rango ${preview.date_range_start} a ${preview.date_range_end}.${preview.warnings.length > 0 ? ` Advertencias: ${preview.warnings.join(" | ")}` : " Sin advertencias."} Preséntame el resumen y dime si debo hacer algo antes de confirmar.`,
      };
      const msgs = [firstMsg];
      setChatMessages(msgs);
      chatMut.mutate({ messages: msgs, summary });
    }
  }, [step, preview]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Tras cargar datos, refrescar dashboard/forecast y mandar al usuario a su Inicio
  useEffect(() => {
    if (step !== "success") return;
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    queryClient.invalidateQueries({ queryKey: ["forecast", "options"] });
    const timer = setTimeout(() => navigate("/dashboard"), 2000);
    return () => clearTimeout(timer);
  }, [step]);

  function sendChat() {
    if (!chatInput.trim() || !preview) return;
    const userMsg: ChatMessage = { role: "user", content: chatInput.trim() };
    const updated = [...chatMessages, userMsg];
    setChatMessages(updated);
    setChatInput("");
    chatMut.mutate({ messages: updated, summary: buildPreviewSummary(preview) });
  }

  const confirmMut = useMutation({
    mutationFn: () => confirmIngest(preview!.records, storeNbr, user?.business_id ?? 1),
    onSuccess: (data) => {
      setSuccessData({ loaded: data.records_loaded, families: data.families, start: data.date_range_start, end: data.date_range_end });
      setStep("success");
    },
  });

  function handleFile(file: File) {
    setFileName(file.name);
    previewMut.mutate(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function reset() {
    setStep("upload");
    setPreview(null);
    setFileName("");
    setChatMessages([]);
    setChatInput("");
    previewMut.reset();
    confirmMut.reset();
  }

  const previewError = previewMut.error as any;
  const confirmError = confirmMut.error as any;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Importar datos de ventas</h2>
        <p className="text-sm text-gray-500">Sube una foto, planilla Excel o PDF — Stocky extrae y ordena los datos automáticamente</p>
      </div>

      {/* Step 1: Upload */}
      {step === "upload" && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-600">Tienda</label>
            <input
              type="number"
              min={1}
              value={storeNbr}
              onChange={e => setStoreNbr(Number(e.target.value))}
              className="w-20 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30"
            />
            <span className="text-xs text-gray-400">Si solo tienes una tienda, deja 1.</span>
          </div>

          <div
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`bg-white p-12 rounded-3xl border-2 border-dashed flex flex-col items-center justify-center text-center space-y-6 cursor-pointer transition-colors ${dragging ? "border-orange-400 bg-orange-50" : "border-gray-200 hover:border-orange-300"}`}
          >
            {previewMut.isPending ? (
              <div className="space-y-4">
                <Loader2 className="w-16 h-16 text-orange-500 animate-spin mx-auto" />
                <p className="text-lg font-bold text-gray-700">Stocky está analizando <span className="text-orange-600">{fileName}</span>...</p>
                <p className="text-sm text-gray-400">Identificando columnas de fecha, familia y ventas</p>
              </div>
            ) : (
              <>
                <div className="w-20 h-20 bg-blue-50 rounded-2xl flex items-center justify-center">
                  <Upload className="w-10 h-10 text-blue-700" />
                </div>
                <div className="space-y-2">
                  <p className="text-xl font-bold text-gray-800">Sube tu archivo de ventas</p>
                  <p className="text-gray-400 text-sm max-w-sm">Arrastra o haz click para seleccionar. Stocky interpreta fotos de cuadernos, Excel desordenados o reportes PDF.</p>
                </div>
                <div className="flex space-x-4">
                  <div className="flex items-center space-x-1 text-[10px] font-bold text-gray-400 uppercase tracking-tighter">
                    <ImageIcon className="w-3 h-3" /> <span>JPG / PNG</span>
                  </div>
                  <div className="flex items-center space-x-1 text-[10px] font-bold text-gray-400 uppercase tracking-tighter">
                    <FileText className="w-3 h-3" /> <span>PDF / XLSX / CSV</span>
                  </div>
                </div>
              </>
            )}
          </div>

          <input ref={inputRef} type="file" accept={ACCEPTED} className="hidden" onChange={e => { if (e.target.files?.[0]) handleFile(e.target.files[0]); }} />

          {previewError && (
            <div className="flex items-start gap-2 bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{previewError.response?.data?.detail ?? "Error al procesar el archivo"}</span>
            </div>
          )}
        </div>
      )}

      {/* Step 2: Preview */}
      {step === "preview" && preview && (
        <div className="space-y-6">
          {/* Summary bar */}
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center shrink-0">
                <CheckCircle className="w-6 h-6 text-green-500" />
              </div>
              <div>
                <p className="font-bold text-gray-800">
                  {preview.records_found} registros extraídos · {preview.store_name}
                </p>
                <p className="text-xs text-gray-500">
                  {preview.date_range_start} → {preview.date_range_end} · {preview.families_detected.length} familias · Tienda {storeNbr}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={reset} className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-xl transition-colors">
                <X className="w-4 h-4" /> Cancelar
              </button>
              <button
                onClick={() => confirmMut.mutate()}
                disabled={confirmMut.isPending || preview.records_found === 0}
                className="flex items-center gap-2 px-5 py-2.5 bg-orange-600 text-white rounded-xl font-semibold hover:opacity-90 disabled:opacity-50 transition-all"
              >
                {confirmMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Confirmar carga
              </button>
            </div>
          </div>

          {/* Warnings */}
          {preview.warnings.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 space-y-1">
              {preview.warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 text-sm text-amber-700">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          )}

          {confirmError && (
            <div className="flex items-start gap-2 bg-red-50 text-red-700 text-sm px-4 py-3 rounded-xl">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{confirmError.response?.data?.detail ?? "Error al confirmar la carga"}</span>
            </div>
          )}

          {/* Stocky chat */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="flex items-center gap-2 px-5 py-3 border-b border-gray-50">
              <div className="w-7 h-7 rounded-lg bg-orange-600 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-semibold text-gray-800">Stocky</span>
              <span className="text-xs text-gray-400">· asistente de ingesta</span>
            </div>

            <div className="px-5 py-4 space-y-3 max-h-64 overflow-y-auto">
              {chatMessages.filter(m => m.role === "assistant").length === 0 && chatMut.isPending && (
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Stocky está revisando los datos...</span>
                </div>
              )}
              {chatMessages.map((m, i) => (
                m.role === "assistant" ? (
                  <div key={i} className="flex items-start gap-2.5">
                    <div className="w-6 h-6 rounded-md bg-orange-600 flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="w-3.5 h-3.5 text-white" />
                    </div>
                    <div className="bg-gray-50 rounded-xl rounded-tl-none px-4 py-2.5 text-sm text-gray-700 max-w-xl leading-relaxed [&_strong]:font-semibold [&_strong]:text-gray-900 [&_ul]:mt-1 [&_ul]:space-y-0.5 [&_li]:ml-4 [&_li]:list-disc [&_p]:mb-1 last:[&_p]:mb-0">
                      <ReactMarkdown>{m.content}</ReactMarkdown>
                    </div>
                  </div>
                ) : i > 0 ? (
                  <div key={i} className="flex justify-end">
                    <div className="bg-orange-600 text-white rounded-xl rounded-tr-none px-4 py-2.5 text-sm max-w-sm leading-relaxed">
                      {m.content}
                    </div>
                  </div>
                ) : null
              ))}
              {chatMut.isPending && chatMessages.length > 0 && (
                <div className="flex items-center gap-2 text-gray-400 text-sm pl-8">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            <div className="px-4 py-3 border-t border-gray-50 flex gap-2">
              <input
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && sendChat()}
                placeholder="Pregúntale algo a Stocky..."
                className="flex-1 px-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500/30"
              />
              <button
                onClick={sendChat}
                disabled={!chatInput.trim() || chatMut.isPending}
                className="px-3 py-2 bg-orange-600 text-white rounded-lg hover:opacity-90 disabled:opacity-40 transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Records table */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    {["Fecha", "Familia", "Ventas", "Promo"].map(h => (
                      <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {preview.records.map((r, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-6 py-3 font-medium text-gray-700">{r.date}</td>
                      <td className="px-6 py-3 text-gray-600">{r.family}</td>
                      <td className="px-6 py-3 font-semibold text-gray-800">{r.sales.toLocaleString("es-CL")}</td>
                      <td className="px-6 py-3">
                        {r.onpromotion ? (
                          <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded font-bold uppercase tracking-tighter">Sí</span>
                        ) : (
                          <span className="text-[10px] text-gray-300">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Success */}
      {step === "success" && successData && (
        <div className="bg-white p-12 rounded-3xl shadow-sm border border-gray-100 text-center space-y-6">
          <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto shadow-xl shadow-green-500/20">
            <CheckCircle className="w-10 h-10 text-white" />
          </div>
          <div className="space-y-2">
            <h3 className="text-2xl font-bold text-gray-800">¡Datos cargados!</h3>
            <p className="text-gray-500">
              <span className="font-semibold text-gray-700">{successData.loaded} registros</span> cargados en tienda {storeNbr} · {successData.start} → {successData.end}
            </p>
            <p className="text-sm text-gray-400">{successData.families.join(", ")}</p>
          </div>
          <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Te llevamos a tu Inicio...</span>
          </div>
        </div>
      )}
    </div>
  );
}
