import React from 'react';

const TopBar = () => {
  return (
    <header className="h-16 bg-white shadow-sm flex items-center justify-between px-8">
      <div className="text-gray-600 font-medium">
        Bienvenido, <span className="text-unab-blue font-bold">Cristóbal</span>
      </div>
      <div className="flex items-center space-x-4">
        <button className="p-2 text-gray-400 hover:text-unab-blue">🔔</button>
        <div className="w-8 h-8 rounded-full bg-unab-light flex items-center justify-center text-white font-bold">
          CF
        </div>
      </div>
    </header>
  );
};

export default TopBar;
