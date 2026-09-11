import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Send, Sparkles, Trash2, X } from "lucide-react";
import { Blobatar } from "@blobatar/react";
import "blobatar/motion.css";
import { happy, wink, thinking, surprised, idle, type Expression } from "blobatar/expression";
import { useAuthStore } from "../../auth/store/authStore";
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
  const user = useAuthStore(s => s.user);
  const businessId = user?.business_id ?? 0;
  const bottomRef = useRef<HTMLDivElement>(null);

  // Ciclo autónomo de vida: Stocky parpadea, sonríe y guiña de forma espontánea sin necesitar cursor
  useEffect(() => {
    if (loading) {
      setExpression(thinking);
      return;
    }

    const interval = setInterval(() => {
      // 45% guiño, 35% feliz, 20% sorpresa curiosa
      const rand = Math.random();
      const nextPose = rand < 0.45 ? wink : rand < 0.8 ? happy : surprised;
      setExpression(nextPose);

      // Mantiene la emoción viva 1.4s y regresa suavemente a idle
      const timeout = setTimeout(() => {
        setExpression(idle);
      }, 1400);

      return () => clearTimeout(timeout);
    }, 3800);

    return () => clearInterval(interval);
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
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
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

  return (
    <>
      {/* Estilos CSS personalizados para darle vida y animación continua a Stocky */}
      <style>{`
        @keyframes stocky-gentle-float {
          0%, 100% {
            transform: translateY(0px) rotate(0deg) scale(1);
          }
          25% {
            transform: translateY(-8px) rotate(-1.5deg) scale(1.03);
          }
          50% {
            transform: translateY(-14px) rotate(0.5deg) scale(1.05);
          }
          75% {
            transform: translateY(-6px) rotate(1.8deg) scale(1.02);
          }
        }

        @keyframes stocky-shadow-scale {
          0%, 100% {
            transform: scale(0.85);
            opacity: 0.25;
          }
          50% {
            transform: scale(1.25);
            opacity: 0.55;
          }
        }

        @keyframes stocky-glow-pulse {
          0%, 100% {
            filter: drop-shadow(0 6px 14px rgba(224, 36, 154, 0.3)) drop-shadow(0 12px 24px rgba(255, 107, 0, 0.25));
          }
          50% {
            filter: drop-shadow(0 12px 26px rgba(224, 36, 154, 0.55)) drop-shadow(0 18px 38px rgba(255, 107, 0, 0.45));
          }
        }

        @keyframes stocky-btn-alive {
          0%, 100% {
            transform: translateY(0) scale(1);
            box-shadow: 0 10px 25px -3px rgba(224, 36, 154, 0.35), 0 4px 10px -2px rgba(255, 107, 0, 0.3);
          }
          50% {
            transform: translateY(-5px) scale(1.04);
            box-shadow: 0 18px 32px -4px rgba(224, 36, 154, 0.55), 0 8px 16px -2px rgba(255, 107, 0, 0.5);
          }
        }

        @keyframes stocky-sparkle-spin {
          0% { transform: translateY(0) rotate(0deg) scale(0.8); opacity: 0.3; }
          50% { transform: translateY(-10px) rotate(180deg) scale(1.2); opacity: 1; }
          100% { transform: translateY(0) rotate(360deg) scale(0.8); opacity: 0.3; }
        }

        .stocky-stage-float {
          animation: stocky-gentle-float 3.6s ease-in-out infinite, stocky-glow-pulse 3.6s ease-in-out infinite;
        }

        .stocky-shadow-pulse {
          animation: stocky-shadow-scale 3.6s ease-in-out infinite;
        }

        .stocky-btn-floating {
          animation: stocky-btn-alive 3.2s ease-in-out infinite;
        }
      `}</style>

      {/* Definición de degradados SVG para la paleta de colores de Stocky */}
      <svg className="absolute w-0 h-0 pointer-events-none" aria-hidden="true" style={{ position: "absolute", width: 0, height: 0 }}>
        <defs>
          <linearGradient id="stocky-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#E0249A" />
            <stop offset="45%" stopColor="#F43F5E" />
            <stop offset="100%" stopColor="#FF6B00" />
          </linearGradient>
          <linearGradient id="stocky-gradient-alt" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#FF6B00" />
            <stop offset="100%" stopColor="#E0249A" />
          </linearGradient>
        </defs>
      </svg>

      {!open && (
        <button
          onClick={() => setOpen(true)}
          onMouseEnter={() => setExpression(happy)}
          onMouseLeave={() => setExpression(idle)}
          title="Preguntar a Stocky"
          className="fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full bg-gradient-to-tr from-[#D91A8D] via-[#F43F5E] to-[#FF6B00] p-1 text-white stocky-btn-floating hover:scale-110 active:scale-95 transition-all flex items-center justify-center shadow-xl shadow-orange-500/35 ring-4 ring-white/95 group"
        >
          {/* Círculo interior blanco para que el cuerpo magenta-naranja y los ojos resalten con nitidez absoluta */}
          <div className="w-full h-full rounded-full bg-white flex items-center justify-center shadow-inner overflow-hidden">
            <div className="w-11 h-11 flex items-center justify-center transition-transform group-hover:scale-115">
              <Blobatar
                name="stocky"
                size={44}
                animate="always"
                expression={expression}
                palette={{ head: "url(#stocky-gradient)", eye: "#1A1A2E" }}
              />
            </div>
          </div>
        </button>
      )}

      {open && (
        <div className="fixed inset-x-4 bottom-4 md:inset-x-auto md:bottom-6 md:right-6 z-50 md:w-96 h-[550px] max-h-[calc(100vh-2rem)] bg-white rounded-3xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3.5 bg-gradient-to-r from-[#D91A8D] via-[#F43F5E] to-[#EA580C] text-white shrink-0 shadow-sm">
            <div
              onClick={() => {
                setExpression(wink);
                setTimeout(() => setExpression(idle), 1500);
              }}
              title="Haz clic para interactuar con Stocky"
              className="w-10 h-10 rounded-full bg-white border border-white/60 flex items-center justify-center overflow-hidden shadow-md shrink-0 cursor-pointer hover:scale-110 active:scale-95 transition-transform"
            >
              <div className="w-8 h-8 flex items-center justify-center">
                <Blobatar
                  name="stocky"
                  size={32}
                  animate="always"
                  expression={expression}
                  palette={{ head: "url(#stocky-gradient)", eye: "#1A1A2E" }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <p className="text-sm font-bold text-white leading-tight">Stocky</p>
                <span className="inline-flex items-center px-1.5 py-0.2 rounded-full text-[10px] font-semibold bg-white/20 text-white border border-white/25">
                  IA
                </span>
              </div>
              <p className="text-[11px] text-white/85">Asistente de inventario</p>
            </div>
            {messages.length > 0 && (
              <button
                onClick={() => setMessages([])}
                title="Borrar historial"
                className="ml-auto p-1.5 hover:bg-white/20 rounded-lg transition-colors active:scale-90"
              >
                <Trash2 className="w-4 h-4 text-white" />
              </button>
            )}
            <button
              onClick={() => setOpen(false)}
              className={`p-1.5 hover:bg-white/20 rounded-lg transition-colors active:scale-90 ${messages.length > 0 ? "" : "ml-auto"}`}
            >
              <X className="w-4 h-4 text-white" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 text-sm mt-2 px-2 select-none">
                {/* Escenario de Stocky con levitación continua y resplandor */}
                <div className="relative w-36 h-36 mx-auto mb-2 flex flex-col items-center justify-center">
                  {/* Resplandor ambiental de la paleta */}
                  <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-[#E0249A]/20 via-[#F43F5E]/20 to-[#FF6B00]/25 blur-2xl animate-pulse" />

                  {/* Chispitas vivas decorativas */}
                  <div className="absolute top-1 right-3 text-pink-400 text-xs animate-[stocky-sparkle-spin_4s_ease-in-out_infinite]">
                    ✨
                  </div>
                  <div className="absolute bottom-6 left-2 text-orange-400 text-xs animate-[stocky-sparkle-spin_3.5s_ease-in-out_infinite_1s]">
                    ✨
                  </div>
                  <div className="absolute top-6 left-3 text-amber-300 text-[11px] animate-[stocky-sparkle-spin_4.5s_ease-in-out_infinite_0.5s]">
                    ✦
                  </div>

                  {/* Mascota con levitación orgánica continua */}
                  <div
                    onClick={() => {
                      setExpression(wink);
                      setTimeout(() => setExpression(idle), 1500);
                    }}
                    onMouseEnter={() => setExpression(happy)}
                    onMouseLeave={() => setExpression(idle)}
                    title="¡Haz clic para interactuar con Stocky!"
                    className="relative cursor-pointer transition-transform active:scale-95 stocky-stage-float z-10"
                  >
                    <div className="w-28 h-28 flex items-center justify-center">
                      <Blobatar
                        name="stocky"
                        size={112}
                        animate="always"
                        expression={expression}
                        palette={{ head: "url(#stocky-gradient)", eye: "#1A1A2E" }}
                      />
                    </div>
                  </div>

                  {/* Sombra proyectada que reacciona a la altura de la levitación */}
                  <div className="w-20 h-3 rounded-full bg-gradient-to-r from-pink-500/20 via-orange-500/30 to-pink-500/20 blur-xs stocky-shadow-pulse -mt-1" />
                </div>

                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-pink-50 to-orange-50 border border-orange-200/60 mb-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[11px] font-semibold text-orange-950">¡Stocky está en línea y activo!</span>
                </div>

                <p className="font-bold text-gray-800 text-base">¡Hola, soy Stocky!</p>
                <p className="mt-1 text-xs text-gray-500 leading-relaxed max-w-xs mx-auto">
                  Puedo revisar qué parámetros faltan en tus productos, ver el stock actual y sugerirte órdenes óptimas.
                </p>

                <div className="mt-3 space-y-1.5 text-left">
                  {suggestions.map(s => (
                    <button
                      key={s}
                      onClick={() => setInput(s)}
                      className="w-full text-left px-3.5 py-2 text-xs bg-gray-50/90 hover:bg-gradient-to-r hover:from-pink-50/70 hover:to-orange-50/70 hover:border-orange-200 hover:text-orange-950 rounded-xl transition-all border border-gray-100 flex items-center justify-between group shadow-2xs"
                    >
                      <span>{s}</span>
                      <Sparkles className="w-3.5 h-3.5 text-orange-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : "justify-start items-start"}`}>
                {m.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-white p-0.5 border border-orange-200 shadow-sm overflow-hidden flex items-center justify-center mt-0.5 shrink-0 hover:scale-110 transition-transform">
                    <Blobatar
                      name="stocky"
                      size={28}
                      animate="always"
                      expression={happy}
                      palette={{ head: "url(#stocky-gradient)", eye: "#1A1A2E" }}
                    />
                  </div>
                )}
                <div className={`max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm whitespace-pre-wrap leading-relaxed ${
                  m.role === "user"
                    ? "bg-gradient-to-r from-[#D91A8D] to-[#EA580C] text-white rounded-br-xs shadow-2xs"
                    : "bg-gray-100 text-gray-800 rounded-tl-xs border border-gray-100"
                }`}>
                  {m.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-2 justify-start items-center">
                <div className="w-8 h-8 rounded-full bg-white p-0.5 border border-orange-200 shadow-sm overflow-hidden flex items-center justify-center animate-bounce shrink-0">
                  <Blobatar
                    name="stocky"
                    size={28}
                    animate="always"
                    expression={thinking}
                    palette={{ head: "url(#stocky-gradient)", eye: "#1A1A2E" }}
                  />
                </div>
                <div className="bg-gray-100 rounded-2xl rounded-tl-xs px-3.5 py-2.5 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-orange-600" />
                  <span className="text-xs text-gray-500 font-medium">Stocky está analizando los datos...</span>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-gray-100 shrink-0 bg-white">
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={e => {
                  setInput(e.target.value);
                  if (expression === idle) {
                    setExpression(happy);
                    setTimeout(() => setExpression(idle), 1200);
                  }
                }}
                onKeyDown={handleKey}
                placeholder="Pregunta algo o da una instrucción..."
                rows={1}
                className="flex-1 resize-none text-sm border border-gray-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-orange-500/40 max-h-24 leading-relaxed"
              />
              <button
                onClick={send}
                disabled={!input.trim() || loading}
                className="p-2.5 bg-gradient-to-r from-[#D91A8D] to-[#FF6B00] text-white rounded-xl hover:opacity-90 active:scale-95 disabled:opacity-40 transition-all shadow-sm shrink-0"
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
