import React from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";
import StockyFloat from "../StockyFloat";

const AppShell = ({ children }) => {
  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden w-full">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
      <StockyFloat />
    </div>
  );
};

export default AppShell;
