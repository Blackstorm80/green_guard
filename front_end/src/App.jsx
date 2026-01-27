// App.jsx
import { Routes, Route } from "react-router-dom";
import DashboardLayout from "./layouts/DashboardLayout";

import HomeTableauDeBord from "./Pages/homeTableauDeBord/homeTableauDeBord";
import EspacesEtSites from "./Pages/espacesEtSites/espaceEtSites";
import Catalogues from "./Pages/catalogues/catalogues";
import Alertes from "./Pages/alertes/alerts";
import Parametres from "./Pages/parametres/parametres";

function App() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route path="/" element={<HomeTableauDeBord />} />
        <Route path="/espacesEtSites" element={<EspacesEtSites />} />
        <Route path="/catalogues" element={<Catalogues />} />
        <Route path="/alertes" element={<Alertes />} />
        <Route path="/parametres" element={<Parametres />} />
      </Route>
    </Routes>
  );
}

export default App;
