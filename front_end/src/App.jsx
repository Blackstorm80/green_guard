import { Routes, Route } from "react-router-dom";
import DashboardLayout from "./layouts/DashboardLayout";
import ProtectedRoute from "./components/auth/ProtectedRoute"; // Le garde-fou
import Login from "./Pages/login/Login"; // La page de connexion

// Imports des Pages existantes
import HomeTableauDeBord from "./Pages/homeTableauDeBord/homeTableauDeBord";
import EspacesEtSites from "./Pages/espacesEtSites/espaceEtSites";
import Catalogues from "./Pages/catalogues/catalogues";
import Rapports from "./Pages/rapports/rapports";

// Placeholder pour les pages en construction
const PageEnConstruction = ({ title }) => (
  <div className="flex flex-col items-center justify-center h-[50vh] text-slate-500 animate-in fade-in duration-500">
    <h2 className="text-xl font-bold text-slate-300">{title}</h2>
    <p>Cette page est en cours de refonte.</p>
  </div>
);

function App() {
  return (
    <Routes>
      {/* 1. Route Publique: Page de Connexion */}
      <Route path="/login" element={<Login />} />

      {/* 2. Routes Protégées: Toutes les autres pages de l'application */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<HomeTableauDeBord />} />
          <Route path="/espaces" element={<EspacesEtSites />} />
          <Route path="/catalogues" element={<Catalogues />} />
          <Route path="/rapports" element={<Rapports />} />
          <Route path="/parametres" element={<PageEnConstruction title="Paramètres" />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;