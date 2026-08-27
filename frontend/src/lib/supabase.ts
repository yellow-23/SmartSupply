import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!url || !anonKey) {
  throw new Error('Faltan VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY en el entorno');
}

// "Recordarme": marcado guarda la sesion en localStorage (sobrevive a cerrar el navegador),
// sin marcar la guarda en sessionStorage (se pierde al cerrar la pestana/navegador).
// setRememberMe() se llama antes de login/signUp para elegir donde escribe esta corrida.
let rememberMe = true;

export function setRememberMe(remember: boolean) {
  rememberMe = remember;
}

const dynamicStorage = {
  getItem: (key: string) => sessionStorage.getItem(key) ?? localStorage.getItem(key),
  setItem: (key: string, value: string) => {
    if (rememberMe) {
      localStorage.setItem(key, value);
      sessionStorage.removeItem(key);
    } else {
      sessionStorage.setItem(key, value);
      localStorage.removeItem(key);
    }
  },
  removeItem: (key: string) => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  },
};

export const supabase = createClient(url, anonKey, {
  auth: { storage: dynamicStorage },
});
