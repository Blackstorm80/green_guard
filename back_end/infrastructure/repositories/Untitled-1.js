import { useState, useEffect } from "react";
import { Search, Plus, MapPin, Leaf, MoreVertical, LayoutGrid, List } from "lucide-react";

// Correction ici : on remonte de deux niveaux (../../) pour atteindre src/
import { api } from "../../services/api";

export default function EspacesSites() {
  const [espaces, setEspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [viewMode, setViewMode] = useState("grid");

  useEffect(() => {
    loadEspaces();
  }, []);

  const loadEspaces = async () => {
    setLoading(true);
    try {
      // Appel de la fonction corrigee dans api.js
      const data = await api.getEspacesVerts();
      setEspaces(data);
    } catch (err) {
      console.error("Erreur lors du chargement des sites :", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredEspaces = espaces.filter(e => 
    e.nom.toLowerCase().includes(search.toLowerCase()) ||
    e.localisation.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Espaces & Sites</h1>
          <p className="text-slate-400 mt-1">{espaces.length} sites enregistres</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="bg-slate-800 p-1 rounded-lg flex border border-slate-800">
            <button 
              onClick={() => setViewMode("grid")}
              className={`p-2 rounded-md transition-all ${viewMode === "grid" ? "bg-slate-700 text-white shadow-lg" : "text-slate-500"}`}
            >
              <LayoutGrid size={18} />
            </button>
            <button 
              onClick={() => setViewMode("list")}
              className={`p-2 rounded-md transition-all ${viewMode === "list" ? "bg-slate-700 text-white shadow-lg" : "text-slate-500"}`}
            >
              <List size={18} />
            </button>
          </div>
          <button className="flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white px-5 py-2.5 rounded-xl font-bold transition-all shadow-lg">
            <Plus size={18} />
            Nouveau Site
          </button>
        </div>
      </div>

      <div className="relative group">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-green-500 transition-colors" size={20} />
        <input 
          type="text"
          placeholder="Rechercher un site..."
          className="w-full bg-slate-900 border border-slate-800 rounded-2xl py-4 pl-12 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-64 bg-slate-800/50 rounded-2xl animate-pulse"></div>
          ))}
        </div>
      ) : (
        <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" : "flex flex-col gap-4"}>
          {filteredEspaces.map((espace) => (
            <div key={espace.id} className="group bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden hover:border-green-500/50 transition-all cursor-pointer">
              <div className="h-40 bg-slate-800 relative">
                <div className="absolute top-4 left-4 bg-slate-950/80 backdrop-blur-md px-3 py-1 rounded-full border border-white/10 flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-[10px] font-bold text-white uppercase">Actif</span>
                </div>
              </div>
              <div className="p-5">
                <h3 className="text-xl font-bold text-white mb-2">{espace.nom}</h3>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-slate-400 text-sm">
                    <MapPin size={14} />
                    <span>{espace.localisation}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-400 text-sm">
                    <Leaf size={14} />
                    <span>{espace.superficie} m2</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}