import api from '../../../shared/api/axios.instance';
import { supabase, setRememberMe } from '../../../shared/lib/supabase';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  name: string;
  email: string;
  role: 'platform_admin' | 'business_admin' | 'analyst';
  business_id: number | null;
  business_name: string;
  onboarding_completed: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  isLoading: boolean;
  error: string | null;
  activeBusinessId: number | null;
  setActiveBusiness: (id: number) => void;
  login: (email: string, password: string, remember?: boolean) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  register: (name: string, email: string, password: string, businessName: string) => Promise<{ needsEmailConfirmation: boolean }>;
  logout: () => Promise<void>;
  syncProfile: () => Promise<void>;
  completeOnboarding: (businessName: string) => Promise<void>;
}

async function fetchProfile(): Promise<User> {
  const { data } = await api.get('/auth/me');
  return data;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isInitialized: false,
      isLoading: false,
      error: null,
      activeBusinessId: null,

      setActiveBusiness: (id) => set({ activeBusinessId: id }),

      login: async (email, password, remember = true) => {
        set({ isLoading: true, error: null });
        try {
          setRememberMe(remember);
          const { error } = await supabase.auth.signInWithPassword({ email, password });
          if (error) throw error;
          const user = await fetchProfile();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (err: any) {
          set({ isLoading: false, error: err.message ?? 'Error al iniciar sesión' });
          throw err;
        }
      },

      loginWithGoogle: async () => {
        const { error } = await supabase.auth.signInWithOAuth({
          provider: 'google',
          options: { redirectTo: `${window.location.origin}/dashboard` },
        });
        if (error) set({ error: error.message });
        // El browser redirige a Google; el resto lo maneja syncProfile() al volver.
      },

      register: async (name, email, password, businessName) => {
        set({ isLoading: true, error: null });
        try {
          const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: { data: { full_name: name, business_name: businessName } },
          });
          if (error) throw error;
          // Supabase no devuelve error si el correo ya existe (para no filtrar cuentas): lo marca con identities vacio.
          if (data.user && data.user.identities?.length === 0) {
            throw new Error('Este correo ya está registrado. Inicia sesión o recupera tu contraseña.');
          }
          if (!data.session) {
            // Confirmacion de email activada en Supabase: todavia no hay sesion.
            set({ isLoading: false });
            return { needsEmailConfirmation: true };
          }
          const user = await fetchProfile();
          set({ user, isAuthenticated: true, isLoading: false });
          return { needsEmailConfirmation: false };
        } catch (err: any) {
          set({ isLoading: false, error: err.message ?? 'Error al registrarse' });
          throw err;
        }
      },

      logout: async () => {
        await supabase.auth.signOut();
        set({ user: null, isAuthenticated: false, error: null, activeBusinessId: null });
      },

      completeOnboarding: async (businessName) => {
        const { data } = await api.post('/auth/onboarding', { business_name: businessName });
        set({ user: data });
      },

      syncProfile: async () => {
        const { data } = await supabase.auth.getSession();
        if (!data.session) {
          set({ user: null, isAuthenticated: false, isInitialized: true });
          return;
        }
        try {
          const user = await fetchProfile();
          set({ user, isAuthenticated: true, isInitialized: true });
        } catch {
          set({ user: null, isAuthenticated: false, isInitialized: true });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated, activeBusinessId: state.activeBusinessId }),
    }
  )
);

// Negocio sobre el que trabajan Dashboard/Forecast/Inventario/Ordenes/Stocky (CU-07).
// Si el usuario nunca eligio otro, es su negocio principal.
export function useActiveBusinessId(): number | null {
  return useAuthStore((s) => s.activeBusinessId ?? s.user?.business_id ?? null);
}

// Mantiene el store sincronizado con la sesion real de Supabase (login, logout, refresh de token,
// y el regreso del redirect de Google OAuth). onAuthStateChange dispara un evento INITIAL_SESSION
// apenas el SDK termina de procesar la sesion (incluye el hash del redirect de OAuth) -- ProtectedRoute
// espera isInitialized antes de decidir si redirige a /login, para no correr esa carrera.
supabase.auth.onAuthStateChange(() => {
  useAuthStore.getState().syncProfile();
});
