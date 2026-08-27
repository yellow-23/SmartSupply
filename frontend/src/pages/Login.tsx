import { useState } from "react";
import { BarChart3, Eye, EyeOff, TrendingUp, Package, Zap, Loader2 } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { useNavigate, Link } from "react-router-dom";

export default function Login() {
  const { login, loginWithGoogle, isLoading, error } = useAuthStore((s) => ({
    login: s.login,
    loginWithGoogle: s.loginWithGoogle,
    isLoading: s.isLoading,
    error: s.error,
  }));
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [formData, setFormData] = useState({ email: "", password: "" });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(formData.email, formData.password, rememberMe);
      navigate("/dashboard");
    } catch {
      // error ya en store
    }
  };

  return (
    <div className="w-full min-h-screen flex">
      {/* Left: hero */}
      <div
        className="flex-1 hidden md:flex items-center justify-center p-12 relative overflow-hidden bg-gradient-to-br from-slate-950 from-[0%] via-blue-900 via-[70%] to-orange-600 to-[100%]"
      >
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-64 h-64 rounded-full border border-white/20" />
          <div className="absolute top-40 left-32 w-96 h-96 rounded-full border border-white/10" />
          <div className="absolute bottom-20 right-10 w-48 h-48 rounded-full border border-white/20" />
        </div>

        <div className="text-white max-w-lg relative z-10">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-10 h-10 bg-white/10 border border-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-semibold tracking-wide">SmartSupply</span>
          </div>

          <h1 className="text-5xl font-bold leading-tight mb-6">
            Predicción inteligente de demanda para tu distribuidora.
          </h1>
          <p className="text-white/60 text-lg mb-12">
            Predice cuánto vas a vender y ordena justo lo que necesitas. Menos mercadería parada, menos quiebres de stock.
          </p>

          {/* Feature pills */}
          <div className="flex flex-col gap-3">
            {[
              { icon: TrendingUp, label: "El sistema elige automáticamente el mejor modelo de predicción para cada producto" },
              { icon: Package, label: "Calcula cuánto y cuándo pedir para evitar quiebres de stock sin acumular excesos" },
              { icon: Zap, label: "Sube fotos, Excel o PDFs con tus ventas — la IA extrae los datos en segundos" },
            ].map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-xl px-4 py-3 backdrop-blur-sm">
                <Icon className="w-4 h-4 text-orange-400 shrink-0" />
                <span className="text-sm text-white/80">{label}</span>
              </div>
            ))}
          </div>
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

          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Bienvenido de vuelta</h2>
            <p className="text-gray-500">Ingresa a tu panel de forecasting y reabastecimiento.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Correo electrónico
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="correo@distribuidora.cl"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent outline-none transition-all bg-white text-sm"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Contraseña
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="Ingresa tu contraseña"
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

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-600">Recordarme</span>
              </label>
              <Link to="/forgot-password" className="text-sm font-medium text-orange-600 hover:opacity-80">
                ¿Olvidaste tu contraseña?
              </Link>
            </div>

            {error && (
              <p className="text-sm text-red-600 text-center -mt-1">{error}</p>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 rounded-xl bg-orange-600 font-semibold text-white transition-opacity duration-200 hover:opacity-90 focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
              {isLoading ? "Ingresando..." : "Iniciar sesión"}
            </button>
          </form>

          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs text-gray-400">o</span>
            <div className="flex-1 h-px bg-gray-200" />
          </div>

          <button
            type="button"
            onClick={() => loginWithGoogle()}
            className="w-full py-3 px-4 rounded-xl border border-gray-300 font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center justify-center gap-2 text-sm"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Continuar con Google
          </button>

          <p className="mt-6 text-center text-sm text-gray-500">
            ¿No tienes cuenta?{" "}
            <Link to="/register" className="font-medium text-orange-600 hover:opacity-80">
              Registrarse
            </Link>
          </p>

          <p className="mt-4 text-center text-xs text-gray-400">
            SmartSupply
          </p>
        </div>
      </div>
    </div>
  );
}
