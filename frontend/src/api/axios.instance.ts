import axios from 'axios';
import { supabase } from '../lib/supabase';

// En dev: Vite proxea /api -> localhost:8000 (ver vite.config.ts)
// En producción: VITE_API_URL = https://smartsupply-e6g8.onrender.com/api (DEBE incluir /api)
const BASE = import.meta.env.VITE_API_URL ?? '/api';

const api = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  if (data.session?.access_token) {
    config.headers.Authorization = `Bearer ${data.session.access_token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      await supabase.auth.signOut();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
