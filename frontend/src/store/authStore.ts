import api from '../api/axios.instance';
import { supabase } from '../lib/supabase';
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'analyst';
  business_id: number;
  business_name: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  register: (name: string, email: string, password: string, businessName: string) => Promise<{ needsEmailConfirmation: boolean }>;
  logout: () => Promise<void>;
  syncProfile: () => Promise<void>;
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
      isLoading: false,
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
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
        set({ user: null, isAuthenticated: false, error: null });
      },

      syncProfile: async () => {
        const { data } = await supabase.auth.getSession();
        if (!data.session) {
          set({ user: null, isAuthenticated: false });
          return;
        }
        try {
          const user = await fetchProfile();
          set({ user, isAuthenticated: true });
        } catch {
          set({ user: null, isAuthenticated: false });
        }
      },
    }),
    { name: 'auth-storage', partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }) }
  )
);

// Mantiene el store sincronizado con la sesion real de Supabase (login, logout, refresh de token,
// y el regreso del redirect de Google OAuth).
supabase.auth.onAuthStateChange(() => {
  useAuthStore.getState().syncProfile();
});
