import { useEffect, useState } from "react";
import { BarChart3, Eye, EyeOff, Loader2, ArrowLeft } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { supabase } from "../../../shared/lib/supabase";

export default function ResetPassword() {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkingLink, setCheckingLink] = useState(true);
  const [hasSession, setHasSession] = useState(false);

  useEffect(() => {
    // El link del correo trae el token en el hash de la URL; el SDK de Supabase
    // lo procesa solo al cargar la pagina y establece una sesion temporal.
    const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === "PASSWORD_RECOVERY" || session) {
        setHasSession(true);
        setCheckingLink(false);
      }
    });
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) setHasSession(true);
      setCheckingLink(false);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres");
      return;
    }
    if (password !== confirm) {
      setError("Las contraseñas no coinciden");
      return;
    }

    setIsLoading(true);
    try {
      const { error } = await supabase.auth.updateUser({ password });
      if (error) throw error;
      navigate("/login?reset=ok");
    } catch (err: any) {
      setError(err.message ?? "Error al restablecer la contraseña");
    } finally {
      setIsLoading(false);
    }
  };

  if (checkingLink) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center bg-white">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!hasSession) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center bg-white p-8">
        <div className="max-w-md w-full text-center">
          <p className="text-red-600 font-medium mb-4">Enlace de recuperación inválido o expirado.</p>
          <Link to="/forgot-password" className="text-orange-600 hover:opacity-80 text-sm font-medium">
            Solicitar un nuevo enlace
          </Link>
        </div>
      </div>
    );
  }

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
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-semibold tracking-wide">SmartSupply</span>
          </div>
          <h1 className="text-5xl font-bold leading-tight mb-6">
            Establece tu nueva contraseña.
          </h1>
          <p className="text-white/60 text-lg">
            Elige una contraseña segura de al menos 8 caracteres.
          </p>
        </div>
      </div>

      {/* Right: form */}
      <div className="flex-1 bg-white flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 md:hidden">
            <div className="w-8 h-8 bg-[#1565C0] rounded-lg flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900">SmartSupply</span>
          </div>

          <Link to="/login" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-8">
            <ArrowLeft className="w-4 h-4" />
            Volver al inicio de sesión
          </Link>

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Nueva contraseña</h2>
            <p className="text-gray-500">Ingresa y confirma tu nueva contraseña.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Nueva contraseña
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Mínimo 8 caracteres"
                  required
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent outline-none transition-all bg-white text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="confirm" className="block text-sm font-medium text-gray-700 mb-2">
                Confirmar contraseña
              </label>
              <div className="relative">
                <input
                  type={showConfirm ? "text" : "password"}
                  id="confirm"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  placeholder="Repite la contraseña"
                  required
                  className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent outline-none transition-all bg-white text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
                >
                  {showConfirm ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
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
              {isLoading ? "Guardando..." : "Restablecer contraseña"}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-gray-400">
            SmartSupply &mdash; Tesis UNAB &middot; Ingeniería Civil en Informática
          </p>
        </div>
      </div>
    </div>
  );
}
