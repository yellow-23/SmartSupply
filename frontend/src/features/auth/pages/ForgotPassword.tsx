import { useState } from "react";
import { Loader2, ArrowLeft } from "lucide-react";
import logoSymbol from "../../../assets/svg/smartsupply-symbol.svg";
import { Link } from "react-router-dom";
import { supabase } from "../../../shared/lib/supabase";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setError(null);
    setIsLoading(true);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });
      if (error) throw error;
      setSent(true);
    } catch (err: any) {
      setError(err.message ?? "Error al enviar el correo");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full min-h-screen flex">
      {/* Left: hero */}
      <div className="flex-1 hidden md:flex items-center justify-center p-12 relative overflow-hidden bg-gradient-to-br from-slate-950 from-[0%] via-blue-900 via-[70%] to-orange-600 to-[100%]">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-64 h-64 rounded-full border border-white/20" />
          <div className="absolute top-40 left-32 w-96 h-96 rounded-full border border-white/10" />
          <div className="absolute bottom-20 right-10 w-48 h-48 rounded-full border border-white/20" />
        </div>
        <div className="text-white max-w-lg relative z-10">
          <div className="flex items-center gap-3 mb-10">
            <div className="w-10 h-10 bg-white/10 border border-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <img src={logoSymbol} alt="" className="w-5 h-5" />
            </div>
            <span className="text-lg font-semibold tracking-wide">SmartSupply</span>
          </div>
          <h1 className="text-5xl font-bold leading-tight mb-6">
            Recupera el acceso a tu cuenta.
          </h1>
          <p className="text-white/60 text-lg">
            Te enviaremos un enlace seguro para que puedas restablecer tu contraseña.
          </p>
        </div>
      </div>

      {/* Right: form */}
      <div className="flex-1 bg-white flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 md:hidden">
            <div className="w-8 h-8 bg-[#1565C0] rounded-lg flex items-center justify-center">
              <img src={logoSymbol} alt="" className="w-4 h-4" />
            </div>
            <span className="text-lg font-bold text-gray-900">SmartSupply</span>
          </div>

          <Link to="/login" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-8">
            <ArrowLeft className="w-4 h-4" />
            Volver al inicio de sesión
          </Link>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">¿Olvidaste tu contraseña?</h2>
            <p className="text-gray-500">Ingresa tu correo y te enviaremos un enlace de recuperación.</p>
          </div>

          {sent ? (
            <div className="rounded-xl bg-green-50 border border-green-200 px-5 py-4 text-sm text-green-700">
              <p className="font-medium mb-1">Correo enviado</p>
              <p>Si el correo está registrado, recibirás un enlace de recuperación en los próximos minutos.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Correo electrónico
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="correo@distribuidora.cl"
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent outline-none transition-all bg-white text-sm"
                />
              </div>

              {error && (
                <p className="text-sm text-red-600 text-center">{error}</p>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 rounded-xl bg-orange-600 font-semibold text-white transition-opacity duration-200 hover:opacity-90 focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-60 flex items-center justify-center gap-2"
              >
                {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                {isLoading ? "Enviando..." : "Enviar enlace de recuperación"}
              </button>
            </form>
          )}

          <p className="mt-8 text-center text-xs text-gray-400">
            SmartSupply &mdash; Tesis UNAB &middot; Ingeniería Civil en Informática
          </p>
        </div>
      </div>
    </div>
  );
}
