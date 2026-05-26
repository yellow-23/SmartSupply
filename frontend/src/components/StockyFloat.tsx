import { useEffect, useRef, useState } from "react";
import { Loader2, Send, Sparkles, X } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { chatStocky, StockyMessage } from "../api/stocky";

export default function StockyFloat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<StockyMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const user = useAuthStore(s => s.user);
  const businessId = user?.business_id ?? 0;
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading || !businessId) return;

    const next: StockyMessage[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);

    try {
      const reply = await chatStocky(next, businessId);
      setMessages(prev => [...prev, { role: "assistant", content: reply }]);
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Hubo un error al conectar. Intenta de nuevo.",
      }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          title="Preguntar a Stocky"
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-gradient-to-br from-orange-500 to-orange-600 text-white shadow-lg hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center"
        >
          <Sparkles className="w-6 h-6" />
        </button>
      )}

      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-96 h-[520px] bg-white rounded-2xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-orange-500 to-orange-600 shrink-0">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white leading-tight">Stocky</p>
              <p className="text-xs text-orange-100">Asistente de inventario</p>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="ml-auto p-1.5 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-white" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="text-center text-gray-400 text-sm mt-10 px-4">
                <Sparkles className="w-8 h-8 mx-auto mb-3 opacity-20" />
                <p className="font-medium text-gray-500">Hola, soy Stocky.</p>
                <p className="mt-1 text-xs leading-relaxed">
                  Puedo revisar qué parámetros faltan en tus productos, ver el stock actual, y actualizar valores directamente.
                </p>
                <div className="mt-4 space-y-1.5 text-left">
                  {[
                    "¿Qué productos tienen el costo vacío?",
                    "Pon el lead time de BEBIDAS en 5 días",
                    "¿Cuál es el stock de LÁCTEOS?",
                  ].map(s => (
                    <button
                      key={s}
                      onClick={() => setInput(s)}
                      className="w-full text-left px-3 py-2 text-xs bg-gray-50 hover:bg-orange-50 hover:text-orange-700 rounded-lg transition-colors border border-gray-100"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[82%] rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap leading-relaxed ${
                  m.role === "user"
                    ? "bg-orange-500 text-white rounded-br-sm"
                    : "bg-gray-100 text-gray-800 rounded-bl-sm"
                }`}>
                  {m.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-3 py-2.5">
                  <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-gray-100 shrink-0">
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Pregunta algo o da una instrucción..."
                rows={1}
                className="flex-1 resize-none text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500/30 max-h-24 leading-relaxed"
              />
              <button
                onClick={send}
                disabled={!input.trim() || loading}
                className="p-2 bg-orange-500 text-white rounded-xl hover:bg-orange-600 disabled:opacity-40 transition-colors shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
