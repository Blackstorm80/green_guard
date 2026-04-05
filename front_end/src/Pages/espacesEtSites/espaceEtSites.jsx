
// export default EspacesEtSites;
import { useEffect, useState } from "react";
import FilterBar from "../../components/FilterBar";
import SpacesTable from "../../components/Spaces/SpacesTable";


/* Données Mock (Simulées) */
const spacesMock = [
  { id: 1001, name: "Espace Vert B", city: "Paris", surface: 210, health: "excellent", healthLabel: "Excellent" },
  { id: 1003, name: "Toit Bibliothèque Centrale", city: "Paris", surface: 230, health: "stress", healthLabel: "Stress Hydrique" },
  { id: 1005, name: "Jardin Lyon Centre", city: "Lyon", surface: 180, health: "excellent", healthLabel: "Excellent" },
];

function EspacesEtSites() {
  /* 1. States pour les filtres (États des filtres) */
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [health, setHealth] = useState("");

  /* 2. States pour les données (Données affichées et métadonnées) */
  const [filteredSpaces, setFilteredSpaces] = useState(spacesMock);
  const [cities, setCities] = useState([]);

  /* 3. Récupération des villes (Simulation API) */
  useEffect(() => {
    fetch("https://api.example.com/cities")
      .then((res) => res.json())
      .then((data) => setCities(data))
      .catch(() => {
        // Fallback pour le projet universitaire
        setCities(["Paris", "Lyon", "Marseille"]);
      });
  }, []);

  /* 4. Logique de filtrage automatique (Mise à jour en temps réel) */
  useEffect(() => {
    let result = spacesMock;

    if (search) {
      result = result.filter(
        (s) =>
          s.name.toLowerCase().includes(search.toLowerCase()) ||
          s.id.toString().includes(search)
      );
    }

    if (city && city !== "Tous") {
      result = result.filter((s) => s.city === city);
    }

    if (health && health !== "Tous") {
      result = result.filter((s) => s.health === health);
    }

    setFilteredSpaces(result);
  }, [search, city, health]); // Se déclenche dès qu'un filtre change

  return (
    <div className="flex flex-col gap-6 p-4">
      {/* BARRE DE FILTRE : 
          On passe les états et les fonctions de mise à jour 
      */}
      <FilterBar
        search={search}
        setSearch={setSearch}
        city={city}
        setCity={setCity}
        health={health}
        setHealth={setHealth}
        cities={cities}
      />

      {/* TABLEAU DES ESPACES : 
          Affiche les données filtrées 
      */}
      <div className="bg-gray-800/50 rounded-3xl border border-gray-700 overflow-hidden">
         <SpacesTable spaces={filteredSpaces} />
      </div>

      
    </div>
  );
}

export default EspacesEtSites;
