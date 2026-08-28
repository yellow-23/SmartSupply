import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./features/auth/pages/Login";
import Register from "./features/auth/pages/Register";
import ForgotPassword from "./features/auth/pages/ForgotPassword";
import ResetPassword from "./features/auth/pages/ResetPassword";
import Dashboard from "./features/dashboard/pages/Dashboard";
import Forecast from "./features/forecast/pages/Forecast";
import Inventory from "./features/inventory/pages/Inventory";
import Ingest from "./features/ingest/pages/Ingest";
import Datos from "./features/datos/pages/Datos";
import Orders from "./features/orders/pages/Orders";
import Products from "./features/products/pages/Products";
import AppShell from "./shared/layout/AppShell";
import ProtectedRoute from "./shared/layout/ProtectedRoute";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppShell>
                <Routes>
                  <Route path="/dashboard"      element={<Dashboard />} />
                  <Route path="/forecasting"    element={<Forecast />} />
                  <Route path="/inventory"      element={<Inventory />} />
                  <Route path="/ingest"         element={<Ingest />} />
                  <Route path="/datos"          element={<Datos />} />
                  <Route path="/orders"         element={<Orders />} />
                  <Route path="/products"       element={<Products />} />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </AppShell>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
