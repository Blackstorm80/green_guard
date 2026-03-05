import { useState, useMemo } from "react";
import { 
  Search, 
  Droplets, 
  Sun, 
  Sprout, 
  Info, 
  Leaf
} from "lucide-react";
import { cn } from "../../lib/utils";

// --- DONNÉES DU CATALOGUE (Base de connaissance) ---
const PLANT_DB = [
  {
    id: 1,
    name: "Érable Champêtre",
    latin: "Acer campestre",
    type: "Arbre",
    water: "LOW", 
    sun: "SUN",
    imageUrl: "https://images.unsplash.com/photo-1598460678822-29df342cb48d?q=80&w=800&auto=format&fit=crop",
    tags: ["Mellifère", "Haie"]
  },
  {
    id: 2,
    name: "Lavande Officinale",
    latin: "Lavandula angustifolia",
    type: "Arbuste",
    water: "LOW",
    sun: "SUN",
    imageUrl: "https://images.unsplash.com/photo-1566808796120-1a738c64c7cc?q=80&w=800&auto=format&fit=crop",
    tags: ["Sécheresse", "Persistant"]
  },
  {
    id: 3,
    name: "Hortensia",
    latin: "Hydrangea macrophylla",
    type: "Arbuste",
    water: "HIGH",
    sun: "PARTIAL",
    imageUrl: "https://images.unsplash.com/photo-1590452366887-b50a04918eaf?q=80&w=800&auto=format&fit=crop",
    tags: ["Fleurissement"]
  },
  {
    id: 4,
    name: "Fougère Mâle",
    latin: "Dryopteris filix-mas",
    type: "Vivace",
    water: "MEDIUM",
    sun: "SHADE",
    imageUrl: "https://images.unsplash.com/photo-1596716073167-a8706c276b66?q=80&w=800&auto=format&fit=crop",
    tags: ["Ombre"]
  }
];

export default function Catalogues() {
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("ALL");

  const filteredPlants = useMemo(() => {
    return PLANT_DB.filter(plant => {
      const matchSearch = plant.name.toLowerCase().includes(search.toLowerCase()) || 
                          plant.latin.toLowerCase().includes(search.toLowerCase());
      const matchType = filterType === "ALL" || plant.type === filterType;
      return matchSearch && matchType;
    });
  }, [search, filterType]);

  return (
    <div className="space-y-6 animate-in fade-in duration-500 h-full flex flex-col">
      
      {/* --- EN-TÊTE --- */}
      <div className="shrink-0">
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Catalogue Botanique
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Référentiel des espèces et fiches techniques.
        </p>
      </div>

      {/* --- BARRE DE RECHERCHE ET FILTRES --- */}
      <div className="flex flex-col md:flex-row gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl shrink-0">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input 
            type="text"
            placeholder="Rechercher une plante..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 text-slate-200 pl-10 pr-4 py-2 rounded-lg text-sm focus:outline-none focus:border-green-500 transition-all"
          />
        </div>

        <div className="flex gap-2">
          {["ALL", "Arbre", "Arbuste", "Vivace"].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors",
                filterType === type 
                  ? "bg-green-600 text-white border-green-500" 
                  : "bg-slate-800 text-slate-400 border-slate-700 hover:text-white"
              )}
            >
              {type === "ALL" ? "Tout" : type}
            </button>
          ))}
        </div>
      </div>

      {/* --- GRILLE DES PLANTES --- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 overflow-y-auto pr-2 custom-scrollbar">
        {filteredPlants.map((plant) => (
          <div 
            key={plant.id}
            className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-600 transition-all group flex flex-col"
          >
            {/* Image */}
            <div className="h-40 overflow-hidden relative">
              <img 
                src={plant.imageUrl} 
                alt={plant.name}
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
              />
              <div className="absolute top-2 right-2 bg-slate-900/80 backdrop-blur-md px-2 py-1 rounded-md text-[10px] font-bold text-white border border-white/10">
                {plant.type}
              </div>
            </div>

            {/* Détails */}
            <div className="p-4 flex-1 flex flex-col">
              <h3 className="font-bold text-slate-100 group-hover:text-green-400 transition-colors text-lg">
                {plant.name}
              </h3>
              <p className="text-xs text-slate-500 italic mb-4 font-serif">
                {plant.latin}
              </p>

              {/* Badges Info */}
              <div className="flex gap-2 mb-4">
                <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-blue-500/10 text-blue-400 text-[10px] font-bold border border-blue-500/20">
                  <Droplets size={12} /> {plant.water}
                </div>
                <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-amber-500/10 text-amber-400 text-[10px] font-bold border border-amber-500/20">
                  <Sun size={12} /> {plant.sun}
                </div>
              </div>

              <button className="w-full mt-auto bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold py-2 rounded-lg transition-colors border border-slate-700 flex items-center justify-center gap-2">
                <Info size={14} /> Fiche Technique
              </button>
            </div>
          </div>
        ))}

        {filteredPlants.length === 0 && (
          <div className="col-span-full py-20 text-center text-slate-500">
            <Sprout size={48} className="mx-auto mb-3 opacity-20" />
            <p>Aucune plante trouvée.</p>
          </div>
        )}
      </div>
    </div>
  );
}