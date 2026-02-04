import { useState } from "react";
import PlantFilterBar from "../../components/Catalogues/PlantFilterBar";
import PlantsGrid from "../../components/Catalogues/PlantsGrid";

const plantsMock = [
  {
    id: 1,
    name: "Sedum acre",
    type: "Couvre-sol • Toits végétalisés",
    water: "Faible",
    exposure: "Soleil",
    icon: "🌾",
  },
  {
    id: 2,
    name: "Fougère (Dryopteris)",
    type: "Vivace • Murs ombragés",
    water: "Élevé",
    exposure: "Ombre",
    icon: "🌿",
  },
  {
    id: 3,
    name: "Lavande",
    type: "Arbuste • Jardins secs",
    water: "Faible",
    exposure: "Soleil",
    icon: "🌸",
  },
];

function Catalog() {
  const [search, setSearch] = useState("");
  const [water, setWater] = useState("");
  const [exposure, setExposure] = useState("");
  const [plants, setPlants] = useState(plantsMock);

  const handleFilter = () => {
    let filtered = plantsMock;

    if (search) {
      filtered = filtered.filter((p) =>
        p.name.toLowerCase().includes(search.toLowerCase()),
      );
    }
    if (water) filtered = filtered.filter((p) => p.water === water);
    if (exposure) filtered = filtered.filter((p) => p.exposure === exposure);

    setPlants(filtered);
  };

  return (
    <div className="flex flex-col gap-6">
      <PlantFilterBar
        search={search}
        setSearch={setSearch}
        water={water}
        setWater={setWater}
        exposure={exposure}
        setExposure={setExposure}
        onFilter={handleFilter}
      />

      <PlantsGrid plants={plants} />
    </div>
  );
}

export default Catalog;
