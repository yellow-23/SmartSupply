import React, { useState } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import StockyFloat from "../StockyFloat";

const AppShell = ({ children }) => {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden w-full">
      <Sidebar open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <TopBar onMenuClick={() => setMobileNavOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          {children}
        </main>
      </div>
      <StockyFloat />
    </div>
  );
};

export default AppShell;
