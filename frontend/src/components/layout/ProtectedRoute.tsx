import { type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

interface ProtectedRouteProps {
  children: ReactNode;
  allowedRoles?: Array<'admin' | 'analyst'>;
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isInitialized = useAuthStore((s) => s.isInitialized);
  const user = useAuthStore((s) => s.user);

  // Evita redirigir a /login antes de que Supabase termine de procesar la sesion
  // (carga inicial de la app, o el regreso del redirect de Google OAuth).
  if (!isInitialized) {
    return (
      <div className="w-full min-h-screen flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-gray-300 border-t-[#1565C0] rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (allowedRoles && user && !allowedRoles.includes(user.role as 'admin' | 'analyst')) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
