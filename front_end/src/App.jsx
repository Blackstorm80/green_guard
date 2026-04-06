import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from './context/AuthContext'; // On garde l'import

// Layouts & Guards
import DashboardLayout from "./layouts/DashboardLayout";
import ProtectedRoute from "./components/auth/ProtectedRoute";

// Pages
import Login from "./Pages/login/Login";
import Register from "./Pages/login/Register";
import HomeTableauDeBord from "./Pages/homeTableauDeBord/homeTableauDeBord";
import EspacesEtSites from "./Pages/espacesEtSites/espaceEtSites";
import Catalogues from "./Pages/catalogues/catalogues";
import Rapports from "./Pages/rapports/rapports";

function App() {
  return (
    // ON ENVELOPPE TOUT ICI
    <AuthProvider> 
      <Routes>
        {/* --- ZONE PUBLIQUE --- */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* --- ZONE PRIVÉE --- */}
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<HomeTableauDeBord />} />
            <Route path="/espaces" element={<EspacesEtSites />} />
            <Route path="/catalogues" element={<Catalogues />} />
            <Route path="/rapports" element={<Rapports />} />
          </Route>
        </Route>

        {/* CATCH-ALL */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;