import { useState } from "react";
import { BarChart3, Loader2 } from "lucide-react";
import { useAuthStore } from "../../store/authStore";

export default function OnboardingGate() {
  const completeOnboarding = useAuthStore((s) => s.completeOnboarding);
  const [businessName, setBusinessName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!businessName.trim()) return;
    setError(null);
    setIsLoading(true);
    try {
      await completeOnboarding(businessName.trim());
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Error al guardar el negocio");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <div className="w-10 h-10 bg-[#1565C0] rounded-xl flex items-center justify-center mb-6">
          <BarChart3 className="w-5 h-5 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">¿Cómo se llama tu distribuidora?</h2>
        <p className="text-gray-500 mb-6 text-sm">
          Un último paso antes de entrar — vamos a usar este nombre en tus reportes y en el panel.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            value={businessName}
            onChange={(e) => setBusinessName(e.target.value)}
            placeholder="Distribuidora El Ahorro"
            autoFocus
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent outline-none transition-all bg-white text-sm"
          />

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={isLoading || !businessName.trim()}
            className="w-full py-3 px-4 rounded-xl bg-orange-600 font-semibold text-white transition-opacity duration-200 hover:opacity-90 focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            {isLoading ? "Guardando..." : "Continuar"}
          </button>
        </form>
      </div>
    </div>
  );
}
