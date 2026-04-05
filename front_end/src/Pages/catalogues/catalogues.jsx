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
    imageUrl: "https://cdn.pixabay.com/photo/2017/07/13/10/33/sedum-2499990_1280.jpg",
    icon: "🌾",
  },
  {
    id: 2,
    name: "Fougère (Dryopteris)",
    type: "Vivace • Murs ombragés",
    water: "Élevé",
    exposure: "Ombre",
    imageUrl: "https://images.pexels.com/photos/673857/pexels-photo-673857.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    icon: "🌿",
  },
  {
    id: 3,
    name: "Lavande",
    type: "Arbuste • Jardins secs",
    water: "Faible",
    exposure: "Soleil",
    imageUrl: "https://images.pexels.com/photos/1166209/pexels-photo-1166209.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    icon: "🌸",
  },
  {
    id: 4,
    name: "Aloe Vera",
    type: "Plante grasse • Intérieur/Extérieur",
    water: "Faible",
    exposure: "Soleil",
    imageUrl: "https://images.pexels.com/photos/167664/pexels-photo-167664.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    icon: "🌵",
  },
  {
    id: 5,
    name: "Hortensia",
    type: "Arbuste • Massifs",
    water: "Élevé",
    exposure: "Mi-ombre",
    imageUrl: "https://images.pexels.com/photos/4505171/pexels-photo-4505171.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1",
    icon: "💐",
  }
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
