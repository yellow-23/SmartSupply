import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Send, Trash2, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Blobatar } from "@blobatar/react";
import "blobatar/motion.css";
import { happy, wink, thinking, surprised, idle, type Expression } from "blobatar/expression";
import { useActiveBusinessId } from "../../auth/store/authStore";
import { chatStocky, StockyMessage } from "../api/stocky";
import { fetchProducts } from "../../products/api/products";

function storageKey(businessId: number) {
  return `stocky-chat-${businessId}`;
}

function loadHistory(businessId: number): StockyMessage[] {
  try {
    const raw = localStorage.getItem(storageKey(businessId));
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export default function StockyFloat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<StockyMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [expression, setExpression] = useState<Expression>(idle);
  const businessId = useActiveBusinessId() ?? 0;
  const bottomRef = useRef<HTMLDivElement>(null);

  // Vida sutil: cada ~7s guiña o sonríe un instante; mientras responde, piensa
  useEffect(() => {
    if (loading) {
      setExpression(thinking);
      return;
    }
    let timeout: ReturnType<typeof setTimeout>;
    const interval = setInterval(() => {
      setExpression(Math.random() < 0.5 ? wink : happy);
      timeout = setTimeout(() => setExpression(idle), 1100);
    }, 7000);
    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [loading]);

  const productsQuery = useQuery({
    queryKey: ["stocky-families", businessId],
    queryFn: () => fetchProducts({ business_id: businessId, limit: 5 }),
    enabled: !!businessId,
    staleTime: 60_000,
  });
  const families = productsQuery.data?.items.map(p => p.family) ?? [];

  const suggestions = families.length > 0
    ? [
      "¿Qué productos tienen el costo vacío?",
      families[1] ? `Pon el lead time de ${families[1]} en 5 días` : `Pon el lead time de ${families[0]} en 5 días`,
      `¿Cuál es el stock de ${families[0]}?`,
    ]
    : [
      "¿Qué productos tengo configurados?",
      "¿Cómo subo mis primeras ventas?",
      "¿Qué son el punto de reorden y el EOQ?",
    ];

  // Carga el historial guardado al abrir un negocio distinto (o al montar).
  useEffect(() => {
    if (businessId) setMessages(loadHistory(businessId));
  }, [businessId]);

  // Persiste cada cambio de conversacion en localStorage, por negocio.
  useEffect(() => {
    if (!businessId) return;
    try {
      localStorage.setItem(storageKey(businessId), JSON.stringify(messages));
    } catch {
      // localStorage lleno o no disponible (modo privado): no bloquea el chat.
    }
  }, [messages, businessId]);

  useEffect(() => {
    const box = bottomRef.current?.parentElement;
    if (box) box.scrollTo({ top: box.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading || !businessId) return;

    const next: StockyMessage[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);
    setExpression(thinking);

    try {
      const reply = await chatStocky(next, businessId);
      setMessages(prev => [...prev, { role: "assistant", content: reply }]);
      setExpression(happy);
      setTimeout(() => setExpression(idle), 2500);
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Hubo un error al conectar. Intenta de nuevo.",
      }]);
      setExpression(surprised);
      setTimeout(() => setExpression(idle), 2000);
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

  // Mascota en colores de la marca: blanca sobre naranjo (avatares) o naranja sobre blanco (bienvenida)
  const onBrand = { head: "#FFFFFF", eye: "#0F172A" };
  const onWhite = { head: "#EA580C", eye: "#0F172A" };

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          onMouseEnter={() => setExpression(happy)}
          onMouseLeave={() => setExpression(idle)}
          aria-label="Abrir Stocky, asistente de inventario"
          title="Preguntar a Stocky"
          className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full bg-orange-600 hover:bg-orange-700 shadow-lg shadow-slate-900/20 ring-4 ring-white flex items-center justify-center transition-transform hover:-translate-y-0.5 active:scale-95"
        >
          <Blobatar name="stocky" size={36} animate="always" expression={expression} palette={onBrand} />
        </button>
      )}

      {open && (
        <div className="fixed inset-x-4 bottom-4 md:inset-x-auto md:bottom-6 md:right-6 z-50 md:w-96 h-[550px] max-h-[calc(100vh-2rem)] bg-white rounded-2xl shadow-2xl shadow-slate-900/20 border border-gray-200 flex flex-col overflow-hidden">
          {/* Header: mismo slate del sidebar */}
          <div className="flex items-center gap-3 px-4 py-3 bg-slate-950 text-white shrink-0">
            <div className="w-9 h-9 rounded-full bg-orange-600 flex items-center justify-center shrink-0">
              <Blobatar name="stocky" size={26} animate="always" expression={expression} palette={onBrand} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold leading-tight">Stocky</p>
              <p className="text-[11px] text-white/60">Asistente de inventario</p>
            </div>
            {messages.length > 0 && (
              <button
                onClick={() => setMessages([])}
                aria-label="Borrar conversación"
                title="Borrar conversación"
                className="ml-auto p-1.5 text-white/60 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={() => setOpen(false)}
              aria-label="Cerrar Stocky"
              className={`p-1.5 text-white/60 hover:text-white hover:bg-white/10 rounded-lg transition-colors ${messages.length > 0 ? "" : "ml-auto"}`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Mensajes */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50/60">
            {messages.length === 0 && (
              <div className="pt-4 px-1">
                <div className="flex flex-col items-center text-center">
                  <div
                    onMouseEnter={() => setExpression(happy)}
                    onMouseLeave={() => setExpression(idle)}
                    className="w-20 h-20 rounded-full bg-white border border-gray-200 flex items-center justify-center"
                  >
                    <Blobatar name="stocky" size={60} animate="always" expression={expression} palette={onWhite} />
                  </div>
                  <p className="mt-3 font-semibold text-gray-900">Hola, soy Stocky</p>
                  <p className="mt-1 text-xs text-gray-500 leading-relaxed max-w-[17rem]">
                    Reviso qué datos les faltan a tus productos, consulto tu stock y te ayudo a decidir qué pedir.
                  </p>
                </div>

                <p className="mt-5 mb-2 text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Prueba preguntando</p>
                <div className="space-y-1.5">
                  {suggestions.map(s => (
                    <button
                      key={s}
                      onClick={() => setInput(s)}
                      className="w-full text-left px-3 py-2 text-xs text-gray-700 bg-white hover:border-orange-300 hover:text-orange-700 rounded-lg border border-gray-200 transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : "justify-start items-start"}`}>
                {m.role === "assistant" && (
                  <div className="w-7 h-7 rounded-full bg-orange-600 flex items-center justify-center mt-0.5 shrink-0">
                    <Blobatar name="stocky" size={20} animate={false} expression={idle} palette={onBrand} />
                  </div>
                )}
                <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "bg-orange-600 text-white rounded-br-sm whitespace-pre-wrap"
                    : "bg-white text-gray-800 border border-gray-200 rounded-tl-sm space-y-2 [&_ul]:list-disc [&_ol]:list-decimal [&_ul]:pl-4 [&_ol]:pl-4 [&_li]:mt-1 [&_strong]:font-semibold"
                }`}>
                  {m.role === "user" ? m.content : <ReactMarkdown>{m.content}</ReactMarkdown>}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-2 justify-start items-center">
                <div className="w-7 h-7 rounded-full bg-orange-600 flex items-center justify-center shrink-0">
                  <Blobatar name="stocky" size={20} animate="always" expression={thinking} palette={onBrand} />
                </div>
                <div className="bg-white border border-gray-200 rounded-xl rounded-tl-sm px-3 py-2 flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-orange-600" />
                  <span className="text-xs text-gray-500">Revisando tus datos...</span>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Entrada */}
          <div className="p-3 border-t border-gray-100 shrink-0 bg-white">
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Pregunta algo o pide un cambio..."
                aria-label="Mensaje para Stocky"
                rows={1}
                className="flex-1 resize-none text-sm border border-gray-200 rounded-lg px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 max-h-24 leading-relaxed"
              />
              <button
                onClick={send}
                disabled={!input.trim() || loading}
                aria-label="Enviar"
                className="p-2.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg disabled:opacity-40 transition-colors shrink-0"
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
