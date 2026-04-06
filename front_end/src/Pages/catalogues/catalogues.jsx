import { useState, useEffect, useMemo } from "react";
import { api } from "../../services/api";
import { Search, Leaf, Bug, Droplets, Thermometer, Info, AlertCircle } from "lucide-react";

export default function Catalogues() {
  const [data, setData] = useState({ plantes: [], auxiliaires: [] });
  const [activeTab, setActiveTab] = useState("plantes");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 1. Chargement des données (Le Pont)
  useEffect(() => {
    const fetchAllData = async () => {
      try {
        setLoading(true);
        const [plantes, auxiliaires] = await Promise.all([
          api.getCataloguePlantes(),
          api.getCatalogueAuxiliaires()
        ]);
        setData({ plantes, auxiliaires });
      } catch (err) {
        setError("Impossible de charger le catalogue. Vérifiez la connexion au serveur.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAllData();
  }, []);

  // 2. Algorithme de filtrage (Optimisation par useMemo)
  const filteredItems = useMemo(() => {
    const source = activeTab === "plantes" ? data.plantes : data.auxiliaires;
    const filtered = source.filter(item => 
      item.nom_commun?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.nom_scientifique?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    // On affiche les 40 premiers pour garder une fluidité de scroll 100% positive
    return filtered.slice(0, 40); 
  }, [searchTerm, activeTab, data]);

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-500 gap-4">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      <p className="font-medium animate-pulse">Extraction du savoir botanique...</p>
    </div>
  );

  if (error) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-red-400 gap-4">
      <AlertCircle size={48} />
      <p>{error}</p>
    </div>
  );

  return (
    <div className="p-8 space-y-8 animate-in fade-in duration-500">
      
      {/* --- BARRE D'OUTILS (Navigation & Recherche) --- */}
      <div className="flex flex-col xl:flex-row gap-6 justify-between items-center bg-slate-900/40 p-5 rounded-[2rem] border border-slate-800/50 backdrop-blur-md">
        
        {/* Sélecteur de catégorie */}
        <div className="flex bg-slate-950 p-1.5 rounded-2xl border border-slate-800 shadow-inner">
          <button 
            onClick={() => setActiveTab("plantes")}
            className={`px-8 py-3 rounded-xl flex items-center gap-3 font-bold transition-all duration-300 ${
              activeTab === "plantes" ? "bg-green-600 text-white shadow-lg shadow-green-900/40 scale-105" : "text-slate-500 hover:text-white"
            }`}
          >
            <Leaf size={20} /> Plantes <span className="text-xs opacity-60 ml-2">{data.plantes.length}</span>
          </button>
          <button 
            onClick={() => setActiveTab("auxiliaires")}
            className={`px-8 py-3 rounded-xl flex items-center gap-3 font-bold transition-all duration-300 ${
              activeTab === "auxiliaires" ? "bg-blue-600 text-white shadow-lg shadow-blue-900/40 scale-105" : "text-slate-500 hover:text-white"
            }`}
          >
            <Bug size={20} /> Auxiliaires <span className="text-xs opacity-60 ml-2">{data.auxiliaires.length}</span>
          </button>
        </div>

        {/* Barre de recherche dynamique */}
        <div className="relative w-full max-w-2xl group">
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-green-500 transition-colors" size={22} />
          <input 
            type="text"
            placeholder={`Rechercher une espèce dans le catalogue ${activeTab}...`}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-3xl py-5 pl-14 pr-6 text-white focus:ring-2 focus:ring-green-500/50 outline-none transition-all placeholder:text-slate-600 shadow-lg"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* --- GRILLE DE CARTES --- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
        {filteredItems.map((item) => (
          <div key={item.id} className="group relative bg-slate-900/30 border border-slate-800/60 rounded-[2.5rem] p-5 hover:border-green-500/40 hover:bg-slate-900/50 transition-all duration-500">
            
            {/* Image avec Overlay de qualité */}
            <div className="aspect-[4/3] rounded-[2rem] overflow-hidden bg-slate-950 mb-6 relative">
              <img 
                src={item.url_image} 
                alt={item.nom_commun}
                className="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-110 transition-all duration-1000 ease-in-out"
                loading="lazy"
                onError={(e) => { e.target.src = "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?q=80&w=500"; }}
              />
              <div className="absolute top-4 right-4 bg-slate-950/60 backdrop-blur-md p-2 rounded-full text-white/50 opacity-0 group-hover:opacity-100 transition-opacity">
                <Info size={16} />
              </div>
            </div>

            {/* Contenu Texte */}
            <div className="px-2 space-y-3">
              <div>
                <h3 className="text-white text-xl font-black truncate group-hover:text-green-400 transition-colors capitalize">
                  {item.nom_commun}
                </h3>
                <p className="text-slate-500 text-sm italic font-medium truncate">
                  {item.nom_scientifique}
                </p>
              </div>
              
              {/* KPIs (Uniquement pour les plantes) */}
              {activeTab === "plantes" && (
                <div className="flex justify-between items-center pt-5 mt-2 border-t border-slate-800/40">
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 rounded-full text-blue-400 border border-blue-500/10">
                    <Droplets size={14} className="fill-current" />
                    <span className="text-xs font-black">{item.besoin_eau} ml</span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 rounded-full text-emerald-400 border border-emerald-500/10">
                    <Thermometer size={14} />
                    <span className="text-xs font-black">pH {item.ph_ideal}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* État vide */}
      {filteredItems.length === 0 && (
        <div className="flex flex-col items-center justify-center py-32 space-y-4 bg-slate-900/20 rounded-[3rem] border border-dashed border-slate-800">
          <Search size={64} className="text-slate-800" />
          <div className="text-center">
            <p className="text-slate-400 text-lg font-bold">Aucun spécimen trouvé</p>
            <p className="text-slate-600 text-sm">Essayez avec un autre mot-clé ou changez de catégorie.</p>
          </div>
        </div>
      )}
    </div>
  );
}