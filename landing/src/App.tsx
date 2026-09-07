import { motion } from "framer-motion";
import {
  BarChart3,
  Camera,
  PackageCheck,
  TrendingUp,
  Upload,
  Sparkles,
} from "lucide-react";
import lockup from "./assets/svg/smartsupply-lockup.svg";

const APP_URL = "https://app.smart-supply.cl";

const features = [
  {
    icon: Camera,
    title: "Sube tus datos como esten",
    text: "Fotos de cuadernos, excel desordenado, PDFs escaneados. La IA los ordena por vos, sin plantillas.",
  },
  {
    icon: TrendingUp,
    title: "Prediccion de demanda automatica",
    text: "El sistema elige el mejor modelo (ARIMA, Prophet, XGBoost) por cada producto, no uno solo para todo.",
  },
  {
    icon: PackageCheck,
    title: "Ordenes de compra listas",
    text: "Calcula cuanto y cuando pedir con politica de stock (s,S), sin planillas manuales.",
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0 },
};

function App() {
  return (
    <div className="min-h-screen overflow-x-hidden">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <img src={lockup} alt="SmartSupply" className="h-8" />
        <a
          href={APP_URL}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition hover:bg-primary/90"
        >
          Ir a la app
        </a>
      </header>

      <main>
        <section className="mx-auto flex max-w-4xl flex-col items-center px-6 pb-20 pt-16 text-center">
          <motion.span
            initial="hidden"
            animate="show"
            variants={fadeUp}
            className="mb-5 inline-flex items-center gap-1.5 rounded-full bg-accent/10 px-3 py-1 text-sm font-medium text-accent"
          >
            <Sparkles className="h-4 w-4" />
            Ingesta con IA, sin planillas perfectas
          </motion.span>

          <motion.h1
            initial="hidden"
            animate="show"
            variants={fadeUp}
            transition={{ delay: 0.05 }}
            className="text-4xl font-bold leading-tight text-sidebar sm:text-5xl"
          >
            Reabastecimiento inteligente para tu distribuidora
          </motion.h1>

          <motion.p
            initial="hidden"
            animate="show"
            variants={fadeUp}
            transition={{ delay: 0.1 }}
            className="mt-5 max-w-2xl text-lg text-sidebar/70"
          >
            SmartSupply predice cuanto vas a vender por producto y genera tus
            ordenes de compra automaticamente. Cargas tus datos como los
            tengas hoy, nosotros los ordenamos.
          </motion.p>

          <motion.div
            initial="hidden"
            animate="show"
            variants={fadeUp}
            transition={{ delay: 0.15 }}
            className="mt-8 flex flex-col gap-3 sm:flex-row"
          >
            <a
              href={APP_URL}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 font-medium text-white shadow-sm transition hover:bg-primary/90"
            >
              <Upload className="h-4 w-4" />
              Empezar gratis
            </a>
            <a
              href="#features"
              className="inline-flex items-center justify-center rounded-lg border border-sidebar/15 px-6 py-3 font-medium text-sidebar transition hover:bg-sidebar/5"
            >
              Como funciona
            </a>
          </motion.div>
        </section>

        <section id="features" className="bg-surface py-20">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mb-12 text-center">
              <h2 className="text-3xl font-bold text-sidebar">
                Todo lo que necesitas para no quedarte sin stock
              </h2>
              <p className="mt-3 text-sidebar/60">
                Ni sobrando capital inmovilizado en bodega.
              </p>
            </div>

            <div className="grid gap-6 sm:grid-cols-3">
              {features.map(({ icon: Icon, title, text }) => (
                <div
                  key={title}
                  className="rounded-2xl border border-sidebar/10 bg-base p-6"
                >
                  <div className="mb-4 inline-flex rounded-xl bg-primary/10 p-3 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="mb-2 font-semibold text-sidebar">{title}</h3>
                  <p className="text-sm text-sidebar/70">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-4xl px-6 py-20 text-center">
          <div className="mb-4 inline-flex rounded-xl bg-accent/10 p-3 text-accent">
            <BarChart3 className="h-5 w-5" />
          </div>
          <h2 className="text-3xl font-bold text-sidebar">
            Empieza a predecir tu demanda hoy
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sidebar/70">
            Sin instalaciones, sin planillas nuevas. Sube tu primer archivo y
            en minutos tienes tu primer pronostico.
          </p>
          <a
            href={APP_URL}
            className="mt-8 inline-flex items-center justify-center rounded-lg bg-primary px-6 py-3 font-medium text-white shadow-sm transition hover:bg-primary/90"
          >
            Crear cuenta gratis
          </a>
        </section>
      </main>

      <footer className="border-t border-sidebar/10 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-6 text-sm text-sidebar/50 sm:flex-row">
          <span>© {new Date().getFullYear()} SmartSupply</span>
          <a href={APP_URL} className="hover:text-sidebar">
            app.smart-supply.cl
          </a>
        </div>
      </footer>
    </div>
  );
}

export default App;
