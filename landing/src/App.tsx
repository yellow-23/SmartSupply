import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Check } from "lucide-react";
import lockup from "./assets/svg/smartsupply-lockup.svg";

const APP_URL = "https://app.smart-supply.cl";
const EASE = [0.22, 1, 0.36, 1] as const;

function Reveal({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, ease: EASE, delay }}
    >
      {children}
    </motion.div>
  );
}

/* Grafico del hero: historial solido + prediccion punteada, igual a como se ve en Forecast real. */
function ForecastMock() {
  const hist = "M0,72 L20,60 L40,66 L60,44 L80,52 L100,30 L120,38 L140,20";
  const pred = "M140,20 L160,26 L180,14 L200,22 L220,10";
  return (
    <svg viewBox="0 0 220 90" className="w-full h-auto overflow-visible" preserveAspectRatio="none">
      <line x1="0" y1="88" x2="220" y2="88" stroke="var(--ss-line)" strokeWidth="1" />
      <path d={hist} fill="none" stroke="var(--ss-blue)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d={pred} fill="none" stroke="var(--ss-accent)" strokeWidth="2.5" strokeDasharray="1 6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="140" cy="20" r="3" fill="var(--ss-blue)" />
    </svg>
  );
}

function App() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="ss-landing">
      <style>{`
        .ss-landing {
          --ss-ink: oklch(0.22 0.02 55);
          --ss-ink-soft: oklch(0.42 0.02 55);
          --ss-ink-faint: oklch(0.58 0.015 55);
          --ss-paper: oklch(0.985 0.004 55);
          --ss-paper-2: oklch(0.955 0.009 55);
          --ss-line: oklch(0.88 0.012 55);
          --ss-accent: #E65100;
          --ss-accent-deep: #B84300;
          --ss-blue: #1565C0;
          --ss-blue-deep: #0D4A94;
          --ss-good: oklch(0.55 0.11 152);
          --ss-alert: oklch(0.56 0.16 33);
          background: var(--ss-paper);
          color: var(--ss-ink);
          font-family: "Public Sans", ui-sans-serif, system-ui, sans-serif;
          min-height: 100vh;
        }
        .ss-landing h1, .ss-landing h2, .ss-landing h3, .ss-landing .ss-display {
          font-family: "Zilla Slab", Georgia, serif;
          letter-spacing: -0.01em;
        }
        .ss-h1 { font-size: clamp(2.5rem, 2rem + 3.2vw, 4.25rem); line-height: 1.03; font-weight: 600; }
        .ss-h2 { font-size: clamp(1.9rem, 1.6rem + 1.6vw, 2.75rem); line-height: 1.08; font-weight: 600; }
        .ss-h3 { font-size: clamp(1.3rem, 1.2rem + 0.6vw, 1.6rem); line-height: 1.2; font-weight: 600; }
        .ss-lede { font-size: clamp(1.05rem, 1rem + 0.4vw, 1.3rem); line-height: 1.55; color: var(--ss-ink-soft); max-width: 62ch; }
        .ss-body { font-size: 1rem; line-height: 1.6; color: var(--ss-ink-soft); max-width: 68ch; }
        .ss-eyebrow { font-size: 0.8rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ss-accent-deep); }
        .ss-btn-primary {
          background: var(--ss-ink); color: var(--ss-paper);
          font-weight: 600; border-radius: 6px; padding: 0.8rem 1.4rem;
          display: inline-flex; align-items: center; gap: 0.5rem;
          transition: transform 0.2s cubic-bezier(.22,1,.36,1), background 0.2s;
        }
        .ss-btn-primary:hover { background: var(--ss-accent-deep); transform: translateY(-1px); }
        .ss-btn-primary:active { transform: scale(0.97); }
        .ss-btn-ghost {
          color: var(--ss-ink); font-weight: 600; padding: 0.8rem 0.4rem;
          display: inline-flex; align-items: center; gap: 0.4rem; border-bottom: 1px solid var(--ss-line);
          transition: border-color 0.2s, color 0.2s;
        }
        .ss-btn-ghost:hover { border-color: var(--ss-ink); }
        .ss-card { background: var(--ss-paper); border: 1px solid var(--ss-line); border-radius: 14px; }
        .ss-mono-num { font-variant-numeric: tabular-nums; }
      `}</style>

      {/* Nav */}
      <header
        className={`sticky top-0 z-40 transition-all duration-300 ${scrolled ? "backdrop-blur-md" : ""}`}
        style={{
          background: scrolled ? "color-mix(in oklch, var(--ss-paper) 88%, transparent)" : "transparent",
          borderBottom: scrolled ? "1px solid var(--ss-line)" : "1px solid transparent",
        }}
      >
        <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
          <motion.a
            href="/"
            aria-label="Volver al inicio"
            onClick={(e) => {
              e.preventDefault();
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            transition={{ type: "spring", stiffness: 400, damping: 24 }}
          >
            <img src={lockup} alt="SmartSupply" className="h-9" />
          </motion.a>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium" style={{ color: "var(--ss-ink-soft)" }}>
            <a href="#como-funciona" className="hover:text-[var(--ss-ink)] transition-colors">Cómo funciona</a>
            <a href="#producto" className="hover:text-[var(--ss-ink)] transition-colors">Producto</a>
            <a href="#stocky" className="hover:text-[var(--ss-ink)] transition-colors">Stocky</a>
          </nav>
          <div className="flex items-center gap-4">
            <a href={APP_URL} className="hidden sm:inline text-sm font-semibold" style={{ color: "var(--ss-ink-soft)" }}>
              Iniciar sesión
            </a>
            <a href={`${APP_URL}/register`} className="ss-btn-primary text-sm !py-2 !px-4">
              Prueba gratis
            </a>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pt-16 pb-20 md:pt-20 md:pb-28">
        <div className="grid md:grid-cols-[1.1fr_0.9fr] gap-14 items-end">
          <div>
            <motion.p
              className="ss-eyebrow mb-5"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}
            >
              Predicción de demanda para distribuidoras chilenas
            </motion.p>
            <motion.h1
              className="ss-h1 mb-6"
              initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: EASE }}
            >
              Deja de adivinar<br />cuánto vas a vender.
            </motion.h1>
            <motion.p
              className="ss-lede mb-9"
              initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: EASE, delay: 0.1 }}
            >
              SmartSupply lee tus datos —vengan de una foto de cuaderno, un Excel desordenado o un PDF escaneado—
              y usa varios modelos de forecasting para elegir el que mejor predice cada producto. Cuando el stock
              se pone crítico, te avisa antes de que se te acabe.
            </motion.p>
            <motion.div
              className="flex flex-wrap items-center gap-6"
              initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: EASE, delay: 0.2 }}
            >
              <a href={`${APP_URL}/register`} className="ss-btn-primary">
                Prueba gratis <ArrowRight size={16} strokeWidth={2.5} />
              </a>
              <a href="#como-funciona" className="ss-btn-ghost">
                Ver cómo funciona
              </a>
            </motion.div>
            <motion.p
              className="mt-8 text-sm"
              style={{ color: "var(--ss-ink-faint)" }}
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.35 }}
            >
              Sin tarjeta de crédito. Tus datos, no una demo con datos inventados.
            </motion.p>
          </div>

          {/* Mockup del producto real */}
          <motion.div
            initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease: EASE, delay: 0.15 }}
            className="ss-card p-5 shadow-[0_1px_2px_rgba(0,0,0,0.04),0_16px_40px_-24px_rgba(0,0,0,0.25)]"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-xs font-semibold" style={{ color: "var(--ss-ink-faint)" }}>PRONÓSTICO — LÁCTEOS</p>
                <p className="ss-h3 !text-xl mt-0.5">142 uds <span className="text-sm font-normal" style={{ color: "var(--ss-ink-faint)" }}>próximos 7 días</span></p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full" style={{ background: "color-mix(in oklch, var(--ss-good) 15%, white)", color: "var(--ss-good)" }}>
                Prophet · WAPE 8.4%
              </span>
            </div>
            <div className="rounded-lg p-3 mb-4" style={{ background: "var(--ss-paper-2)" }}>
              <ForecastMock />
              <div className="flex items-center gap-4 mt-2 text-xs" style={{ color: "var(--ss-ink-faint)" }}>
                <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 rounded-full" style={{ background: "var(--ss-blue)" }} /> Real</span>
                <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 rounded-full" style={{ background: "var(--ss-accent)" }} /> Predicción</span>
              </div>
            </div>
            <div className="flex items-center justify-between py-3 border-t" style={{ borderColor: "var(--ss-line)" }}>
              <div className="flex items-center gap-2.5">
                <motion.span
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ background: "var(--ss-alert)" }}
                  animate={{ opacity: [1, 0.35, 1] }}
                  transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
                />
                <span className="text-sm font-medium">CONGELADOS — stock crítico (4 uds)</span>
              </div>
              <span className="text-xs font-semibold" style={{ color: "var(--ss-ink-faint)" }}>correo enviado</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y" style={{ borderColor: "var(--ss-line)", background: "var(--ss-paper-2)" }}>
        <div className="mx-auto max-w-6xl px-6 py-14 grid grid-cols-1 sm:grid-cols-3 gap-10">
          {[
            { n: "3", label: "modelos compitiendo por cada producto", sub: "ARIMA, Prophet y XGBoost — gana el de menor error, no el mismo para todo" },
            { n: "24/7", label: "monitoreo de tu stock", sub: "Alertas automáticas por correo apenas un producto entra en zona crítica" },
            { n: "0", label: "planillas que armar a mano", sub: "Sube la foto, el Excel o el PDF tal como los tengas hoy" },
          ].map((s, i) => (
            <Reveal key={s.label} delay={i * 0.08}>
              <p className="ss-display ss-mono-num text-5xl font-semibold" style={{ color: "var(--ss-ink)" }}>{s.n}</p>
              <p className="text-sm font-semibold mt-2 mb-1.5">{s.label}</p>
              <p className="text-sm" style={{ color: "var(--ss-ink-faint)" }}>{s.sub}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Como funciona */}
      <section id="como-funciona" className="mx-auto max-w-6xl px-6 py-24">
        <Reveal className="mb-14 max-w-2xl">
          <p className="ss-eyebrow mb-3">Cómo funciona</p>
          <h2 className="ss-h2">De tus datos reales a una decisión de compra, en cuatro pasos.</h2>
        </Reveal>
        <div className="grid md:grid-cols-4 gap-8">
          {[
            { n: "01", t: "Subes lo que tengas", d: "Foto de un cuaderno, ticket, Excel desordenado o PDF escaneado. No necesitas ordenar nada antes." },
            { n: "02", t: "Extraemos y validamos", d: "El sistema arma fechas, familias y ventas, y te avisa si algo se ve raro antes de cargarlo." },
            { n: "03", t: "El AMS predice", d: "Por cada producto se prueban varios modelos y se usa el que mejor predijo tu historial real." },
            { n: "04", t: "Actúas antes de quedarte sin stock", d: "Alertas de stock crítico, órdenes de compra sugeridas y correos automáticos semanales." },
          ].map((step, i) => (
            <Reveal key={step.n} delay={i * 0.08}>
              <p className="ss-display text-sm font-semibold mb-4" style={{ color: "var(--ss-accent)" }}>{step.n}</p>
              <h3 className="ss-h3 mb-2">{step.t}</h3>
              <p className="text-sm" style={{ color: "var(--ss-ink-faint)" }}>{step.d}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Producto: features con mockups reales */}
      <section id="producto" className="mx-auto max-w-6xl px-6 py-24 border-t" style={{ borderColor: "var(--ss-line)" }}>
        <Reveal className="mb-16 max-w-2xl">
          <p className="ss-eyebrow mb-3">El producto</p>
          <h2 className="ss-h2">Hecho para el negocio que ya tienes, no para uno ideal.</h2>
        </Reveal>

        <div className="space-y-24">
          {/* Feature 1: Ingesta IA */}
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <Reveal>
              <h3 className="ss-h3 mb-3">Ingesta con IA: sube lo que tengas, así como está</h3>
              <p className="ss-body mb-4">
                La mayoría de las distribuidoras chilenas no llevan sus ventas en un sistema. SmartSupply acepta
                fotos de cuadernos y pizarras, Excel desordenados o PDFs escaneados, y los convierte en datos
                normalizados listos para predecir.
              </p>
              <ul className="space-y-2.5 text-sm" style={{ color: "var(--ss-ink-soft)" }}>
                {["Detecta fechas, familias y unidades automáticamente", "Te avisa si hay fechas futuras, huecos o cambios de escala raros", "Revisas el preview antes de confirmar — nunca se carga a ciegas"].map((f) => (
                  <li key={f} className="flex items-start gap-2.5">
                    <Check size={16} className="mt-0.5 flex-shrink-0" style={{ color: "var(--ss-good)" }} />
                    {f}
                  </li>
                ))}
              </ul>
            </Reveal>
            <Reveal delay={0.1}>
              <div className="ss-card p-5">
                <p className="text-xs font-semibold mb-3" style={{ color: "var(--ss-ink-faint)" }}>PREVIEW DE CARGA — ventas_marzo.xlsx</p>
                <div className="space-y-2">
                  {[
                    ["11/03/2025", "LÁCTEOS", "18 uds"],
                    ["11/03/2025", "BEBIDAS", "34 uds"],
                    ["12/03/2025", "ABARROTES", "22 uds"],
                  ].map((row) => (
                    <div key={row[0] + row[1]} className="flex items-center justify-between text-sm py-2 px-3 rounded-md" style={{ background: "var(--ss-paper-2)" }}>
                      <span style={{ color: "var(--ss-ink-faint)" }}>{row[0]}</span>
                      <span className="font-medium">{row[1]}</span>
                      <span className="ss-mono-num">{row[2]}</span>
                    </div>
                  ))}
                </div>
                <div className="flex items-center gap-2 mt-4 pt-4 border-t text-sm" style={{ borderColor: "var(--ss-line)" }}>
                  <Check size={15} style={{ color: "var(--ss-good)" }} />
                  <span>360 filas listas — sin errores de calidad</span>
                </div>
              </div>
            </Reveal>
          </div>

          {/* Feature 2: Inventario + alertas */}
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <Reveal delay={0.1} className="md:order-2">
              <h3 className="ss-h3 mb-3">Sabes qué comprar antes de que sea urgente</h3>
              <p className="ss-body mb-4">
                Cada producto tiene su punto de reorden (política s,S) calculado con tu demanda real, no con una
                regla genérica. Cuando el stock cruza ese punto, se genera una orden de compra sugerida.
              </p>
              <ul className="space-y-2.5 text-sm" style={{ color: "var(--ss-ink-soft)" }}>
                {["Cantidad óptima de pedido (EOQ) por producto y tienda", "Órdenes de compra con seguimiento de estado hasta que llegan", "Reportes en Excel y PDF para compartir con proveedores"].map((f) => (
                  <li key={f} className="flex items-start gap-2.5">
                    <Check size={16} className="mt-0.5 flex-shrink-0" style={{ color: "var(--ss-good)" }} />
                    {f}
                  </li>
                ))}
              </ul>
            </Reveal>
            <Reveal className="md:order-1">
              <div className="ss-card p-5">
                <p className="text-xs font-semibold mb-3" style={{ color: "var(--ss-ink-faint)" }}>ALERTAS DE STOCK</p>
                <div className="space-y-2.5">
                  {[
                    { name: "CONGELADOS", stock: "4 uds", tag: "crítico", color: "var(--ss-alert)" },
                    { name: "PANADERÍA", stock: "12 uds", tag: "bajo", color: "var(--ss-accent-deep)" },
                    { name: "BEBIDAS", stock: "88 uds", tag: "ok", color: "var(--ss-good)" },
                  ].map((r) => (
                    <div key={r.name} className="flex items-center justify-between text-sm py-2.5 px-3 rounded-md" style={{ background: "var(--ss-paper-2)" }}>
                      <span className="font-medium">{r.name}</span>
                      <span className="ss-mono-num" style={{ color: "var(--ss-ink-faint)" }}>{r.stock}</span>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ color: r.color, background: "color-mix(in oklch, " + r.color + " 14%, white)" }}>
                        {r.tag}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* Stocky */}
      <section id="stocky" className="mx-auto max-w-6xl px-6 py-24 border-t" style={{ borderColor: "var(--ss-line)" }}>
        <div className="grid md:grid-cols-2 gap-14 items-center">
          <Reveal>
            <p className="ss-eyebrow mb-3">Tu asistente</p>
            <h2 className="ss-h2 mb-5">Pregúntale a Stocky, no revises cinco pantallas</h2>
            <p className="ss-body mb-4">
              Stocky conoce los datos reales de tu negocio: qué se está vendiendo, qué está por agotarse y qué
              cargas hiciste esta semana. Le preguntas en lenguaje simple y te responde con tus números, no con
              una respuesta genérica.
            </p>
            <p className="ss-body">
              Cada lunes te manda un resumen de la semana. Si un producto se pone crítico, te avisa el mismo día
              por correo — no tienes que estar mirando el dashboard.
            </p>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="ss-card p-5">
              <div className="space-y-3">
                <div className="ml-auto max-w-[80%] text-sm px-4 py-2.5 rounded-2xl rounded-br-sm" style={{ background: "var(--ss-blue)", color: "var(--ss-paper)" }}>
                  ¿cómo viene la semana en lácteos?
                </div>
                <div className="max-w-[85%] text-sm px-4 py-2.5 rounded-2xl rounded-bl-sm" style={{ background: "var(--ss-paper-2)" }}>
                  Vas 12% arriba de la semana pasada. El modelo predice 142 unidades para los próximos 7 días.
                  CONGELADOS sigue en stock crítico (4 uds) — ¿genero la orden de compra?
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* CTA final */}
      <section className="border-t" style={{ borderColor: "var(--ss-line)", background: "var(--ss-ink)" }}>
        <div className="mx-auto max-w-6xl px-6 py-24 text-center">
          <Reveal>
            <h2 className="ss-h2 mb-5" style={{ color: "var(--ss-paper)" }}>
              Prueba con tus propios datos.
            </h2>
            <p className="ss-lede mx-auto mb-9" style={{ color: "color-mix(in oklch, var(--ss-paper) 70%, transparent)" }}>
              Crea tu negocio, sube tu primera carga y en minutos tienes tu primer pronóstico real.
            </p>
            <a
              href={`${APP_URL}/register`}
              className="ss-btn-primary"
              style={{ background: "var(--ss-accent)", color: "var(--ss-ink)" }}
            >
              Prueba gratis <ArrowRight size={16} strokeWidth={2.5} />
            </a>
          </Reveal>
        </div>
      </section>

      {/* Footer */}
      <footer className="mx-auto max-w-6xl px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm" style={{ color: "var(--ss-ink-faint)" }}>
        <img src={lockup} alt="SmartSupply" className="h-5 opacity-80" />
        <span>Predicción de demanda y reabastecimiento para distribuidoras chilenas.</span>
      </footer>
    </div>
  );
}

export default App;
