import React from 'react';

const Login = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-unab-blue">
      <div className="bg-white p-10 rounded-xl shadow-2xl w-full max-w-md">
        <h1 className="text-3xl font-bold text-unab-blue mb-2">SmartSupply</h1>
        <p className="text-gray-500 mb-8">Ingresa tus credenciales para continuar</p>
        <form className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input 
              type="email" 
              className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-unab-light focus:border-unab-light"
              placeholder="usuario@distribuidora.cl"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Contraseña</label>
            <input 
              type="password" 
              className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-unab-light focus:border-unab-light"
              placeholder="••••••••"
            />
          </div>
          <button 
            type="button"
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-unab-light hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-unab-light"
            onClick={() => window.location.href = '/dashboard'}
          >
            Iniciar Sesión
          </button>
        </form>
        <div className="mt-6 text-center">
          <a href="#" className="text-sm text-unab-light hover:underline">¿Olvidaste tu contraseña?</a>
        </div>
      </div>
    </div>
  );
};

export default Login;
