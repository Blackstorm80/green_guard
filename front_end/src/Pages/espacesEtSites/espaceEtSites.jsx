import { useEffect, useState } from "react";
import FilterBar from "../../components/FilterBar";
import SpacesTable from "../../components/Spaces/SpacesTable";

/* داده تست (بعداً از API میاد) */
const spacesMock = [
  {
    id: 1001,
    name: "Espace Vert B",
    city: "Paris",
    surface: 210,
    health: "excellent",
    healthLabel: "Excellent",
  },
  {
    id: 1003,
    name: "Toit Bibliothèque Centrale",
    city: "Paris",
    surface: 230,
    health: "stress",
    healthLabel: "Stress Hydrique",
  },
  {
    id: 1005,
    name: "Jardin Lyon Centre",
    city: "Lyon",
    surface: 180,
    health: "excellent",
    healthLabel: "Excellent",
  },
];

function EspacesEtSites() {
  /* state فیلترها */
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [health, setHealth] = useState("");

  /* state داده‌ها */
  const [spaces, setSpaces] = useState(spacesMock);
  const [cities, setCities] = useState([]);

  /* گرفتن شهرها از API */
  useEffect(() => {
    fetch("https://api.example.com/cities")
      .then((res) => res.json())
      .then((data) => {
        // مثال: ["Paris", "Lyon", "Marseille"]
        setCities(data);
      })
      .catch(() => {
        // fallback برای پروژه دانشگاه 😉
        setCities(["Paris", "Lyon"]);
      });
  }, []);

  /* اعمال فیلتر */
  const handleFilter = () => {
    let filtered = spacesMock;

    if (search) {
      filtered = filtered.filter(
        (s) =>
          s.name.toLowerCase().includes(search.toLowerCase()) ||
          s.id.toString().includes(search),
      );
    }

    if (city) {
      filtered = filtered.filter((s) => s.city === city);
    }

    if (health) {
      filtered = filtered.filter((s) => s.health === health);
    }

    setSpaces(filtered);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* FILTER BAR */}
      <FilterBar
        search={search}
        setSearch={setSearch}
        city={city}
        setCity={setCity}
        health={health}
        setHealth={setHealth}
        cities={cities}
        onFilter={handleFilter}
      />

      {/* TABLE */}
      <SpacesTable spaces={spaces} />
    </div>
  );
}

export default EspacesEtSites;
