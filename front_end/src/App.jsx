import { Routes, Route, Navigate } from "react-router-dom";

// Layouts & garde (l'AuthProvider est monté une seule fois, dans main.jsx)
import DashboardLayout from "./layouts/DashboardLayout";
import ProtectedRoute from "./components/auth/ProtectedRoute";

// Pages
import Login from "./Pages/login/Login";
import Register from "./Pages/login/Register";
import HomeTableauDeBord from "./Pages/homeTableauDeBord/homeTableauDeBord";
import EspacesEtSites from "./Pages/espacesEtSites/espaceEtSites";
import Catalogues from "./Pages/catalogues/catalogues";
import Rapports from "./Pages/rapports/rapports";
import Parametres from "./Pages/parametres/parametres";
import PageIntrouvable from "./Pages/PageIntrouvable";

function App() {
  return (
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
          <Route path="/parametres" element={<Parametres />} />
          <Route path="*" element={<PageIntrouvable />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
