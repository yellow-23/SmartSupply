import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Forecast from "./pages/Forecast";
import Inventory from "./pages/Inventory";
import Ingest from "./pages/Ingest";
import Orders from "./pages/Orders";
import Products from "./pages/Products";
import AppShell from "./components/layout/AppShell";
import { useAuthStore } from "./store/authStore";

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <AppShell>
                <Routes>
                  <Route path="/dashboard"   element={<Dashboard />} />
                  <Route path="/forecasting" element={<Forecast />} />
                  <Route path="/inventory"   element={<Inventory />} />
                  <Route path="/ingest"      element={<Ingest />} />
                  <Route path="/orders"      element={<Orders />} />
                  <Route path="/products"    element={<Products />} />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </AppShell>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
