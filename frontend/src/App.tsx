import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Forecast from "./pages/Forecast";
import Inventory from "./pages/Inventory";
import Ingest from "./pages/Ingest";
import Orders from "./pages/Orders";
import Products from "./pages/Products";
import AppShell from "./components/layout/AppShell";
import ProtectedRoute from "./components/layout/ProtectedRoute";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
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
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
