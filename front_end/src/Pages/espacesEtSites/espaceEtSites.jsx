import { useState, useEffect } from "react";
import { 
  Search, Plus, MapPin, Leaf, LayoutGrid, List, Layers 
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "../../services/api";
import AddSpaceModal from "./AddSpaceModal";
import EditSpaceModal from "./EditSpaceModal"; // 1. Importer le nouveau composant

export default function EspacesSites() {
  const [espaces, setEspaces] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false); // 2. State pour la modale d'édition
  const [selectedEspace, setSelectedEspace] = useState(null); // 2. State pour l'espace sélectionné
  const [search, setSearch] = useState("");
  const [activeClusterId, setActiveClusterId] = useState(null);
  const [viewMode, setViewMode] = useState("grid");

  useEffect(() => {
    chargerDonnees();
  }, []);

  const chargerDonnees = async () => {
    setLoading(true);
    try {
      const [sitesData, clustersData] = await Promise.all([
        api.getEspacesVerts(),
        api.getZones()
      ]);
      setEspaces(sitesData);
      setClusters(clustersData);
    } catch (err) {
      console.error("Erreur chargement :", err);
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = (site) => {
    setSelectedEspace(site);
    setIsEditModalOpen(true);
  };

  const getCouleurSante = (score) => {
    if (score >= 85) return "#0CB95D";
    if (score >= 65) return "#E77C02";
    return "#DF1B1B";
  };

  const sitesFiltres = espaces.filter(site => {
    const matchSearch = site.nom.toLowerCase().includes(search.toLowerCase());
    const matchCluster = !activeClusterId || site.zone_id === activeClusterId;
    return matchSearch && matchCluster;
  });

  const aBesoinDePulse = espaces.length === 0;

  return (
    <div className="relative space-y-8 animate-in fade-in duration-700 pb-20">
      
      {/* HEADER */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Clusters Intelligents</h1>
          <p className="text-slate-400 mt-1">Segmentation basee sur la geographie et la sante</p>
        </div>
        
        <button 
          onClick={() => setIsAddModalOpen(true)}
          className="hidden md:flex items-center gap-2 bg-green-600 hover:bg-green-500 text-white px-5 py-2 rounded-xl font-bold transition-all shadow-lg"
        >
          <Plus size={20} />
          <span>Ajouter un espace</span>
        </button>
      </div>

      {/* SECTION DES JAUGES DE CLUSTERS (inchangée) ... */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          onClick={() => setActiveClusterId(null)}
          className={`cursor-pointer p-4 rounded-2xl border transition-all ${
            !activeClusterId ? "bg-slate-800 border-green-500 shadow-lg" : "bg-slate-900 border-slate-800 hover:border-slate-700"
          }`}
        >
          <div className="flex justify-between items-center">
             <span className="text-xs font-bold text-slate-500 uppercase">Vue Globale</span>
             <Layers size={16} className={!activeClusterId ? "text-green-500" : "text-slate-600"} />
          </div>
          <p className="text-2xl font-black text-white mt-2">{espaces.length}</p>
        </div>

        {clusters.map((cluster) => {
          const couleur = getCouleurSante(cluster.sante_moyenne);
          const isActive = activeClusterId === cluster.id;
          return (
            <div 
              key={cluster.id}
              onClick={() => setActiveClusterId(cluster.id)}
              className={`cursor-pointer p-4 rounded-2xl border transition-all relative overflow-hidden ${
                isActive ? "bg-slate-800 border-white/20 shadow-xl scale-[1.02]" : "bg-slate-900 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex justify-between items-start relative z-10">
                <div className="max-w-[70%]">
                  <span className="text-[10px] font-bold text-slate-500 uppercase truncate block">{cluster.nom}</span>
                  <p className="text-2xl font-black text-white mt-1">{cluster.nb_espaces}</p>
                </div>
                <div className="relative w-12 h-12 flex items-center justify-center">
                   <svg className="w-full h-full transform -rotate-90">
                      <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-slate-800" />
                      <circle 
                        cx="24" cy="24" r="20" stroke={couleur} strokeWidth="4" fill="transparent" 
                        strokeDasharray={125}
                        strokeDashoffset={125 - (125 * cluster.sante_moyenne) / 100}
                        strokeLinecap="round"
                      />
                   </svg>
                   <span className="absolute text-[9px] font-bold text-white">{Math.round(cluster.sante_moyenne)}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* BARRE DE RECHERCHE (inchangée) ... */}
      <div className="flex flex-col md:flex-row gap-4 items-center bg-slate-900/50 p-4 rounded-2xl border border-slate-800">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
          <input 
            type="text"
            placeholder="Rechercher par nom..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl py-3 pl-12 pr-4 text-white outline-none focus:ring-1 focus:ring-green-500"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button onClick={() => setViewMode("grid")} className={`p-2 rounded ${viewMode === "grid" ? "bg-slate-800 text-white" : "text-slate-500"}`}><LayoutGrid size={18} /></button>
          <button onClick={() => setViewMode("list")} className={`p-2 rounded ${viewMode === "list" ? "bg-slate-800 text-white" : "text-slate-500"}`}><List size={18} /></button>
        </div>
      </div>

      {/* LISTE DES SITES */}
      <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" : "space-y-4"}>
        {sitesFiltres.map(site => (
          // 3. Ajouter onClick pour ouvrir la modale d'édition
          <div 
            key={site.id} 
            onClick={() => handleEditClick(site)}
            className="bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-green-500/50 transition-all group cursor-pointer"
          >
            <h3 className="text-xl font-bold text-white mb-1">{site.nom}</h3>
            <div className="flex items-center gap-2 text-slate-500 text-sm mb-4">
              <MapPin size={14} />
              <span>{site.ville}</span>
            </div>
            <div className="pt-4 border-t border-slate-800 flex justify-between items-center text-[10px] text-slate-500 font-bold uppercase">
               <span>Zone: {site.zone_id}</span>
               <span className={site.sante_percent >= 85 ? "text-green-500" : "text-amber-500"}>{site.sante_percent}% Sante</span>
            </div>
          </div>
        ))}
      </div>

      {/* BOUTON MOBILE FLOTTANT (FAB) */}
      <AnimatePresence>
        <motion.button
          initial={{ scale: 0 }}
          animate={{ 
            scale: 1,
            boxShadow: aBesoinDePulse ? ["0px 0px 0px rgba(34,197,94,0)", "0px 0px 20px rgba(34,197,94,0.6)", "0px 0px 0px rgba(34,197,94,0)"] : "none"
          }}
          transition={{ repeat: Infinity, duration: 2 }}
          onClick={() => setIsAddModalOpen(true)}
          className="md:hidden fixed bottom-6 right-6 z-50 bg-green-600 text-white p-4 rounded-full shadow-2xl"
        >
          <Plus size={28} />
        </motion.button>
      </AnimatePresence>

      {/* MODALES */}
      {isAddModalOpen && (
        <AddSpaceModal 
          onClose={() => setIsAddModalOpen(false)} 
          onSuccess={chargerDonnees} 
        />
      )}
      
      {/* 4. Rendu conditionnel de la modale d'édition */}
      {isEditModalOpen && selectedEspace && (
        <EditSpaceModal
          espace={selectedEspace}
          onClose={() => setIsEditModalOpen(false)}
          onSuccess={() => {
            chargerDonnees();
            setIsEditModalOpen(false);
          }}
        />
      )}
    </div>
  );
}