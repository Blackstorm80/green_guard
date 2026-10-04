import { useState, useEffect } from "react";
import { 
  Search, Plus, MapPin, Leaf, LayoutGrid, List, Layers 
} from "lucide-react";
import { api } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import { useTitrePage } from "../../lib/hooks";
import { peut } from "../../lib/referentiels";
import AddSpaceModal from "./AddSpaceModal";
import EditSpaceModal from "./EditSpaceModal"; // 1. Importer le nouveau composant

export default function EspacesSites() {
  useTitrePage("Espaces et zones");
  const { user } = useAuth();
  // Lecteur et technicien consultent le patrimoine sans le modifier
  const peutGerer = peut(user, "gestion");
  const [espaces, setEspaces] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false); // 2. State pour la modale d'édition
  const [selectedEspace, setSelectedEspace] = useState(null); // 2. State pour l'espace sélectionné
  const [search, setSearch] = useState("");
  const [activeClusterId, setActiveClusterId] = useState(null);
  const [viewMode, setViewMode] = useState("grid");
  const [recalcul, setRecalcul] = useState({ enCours: false, message: "" });

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

  const recalculerZones = async () => {
    setRecalcul({ enCours: true, message: "" });
    try {
      const res = await api.rebuildZones();
      setRecalcul({ enCours: false, message: res.message });
      await chargerDonnees();
    } catch (err) {
      setRecalcul({ enCours: false, message: err.message });
    }
  };

  const nomZone = (zoneId) => clusters.find((c) => c.id === zoneId)?.nom ?? "Non regroupé";

  const handleEditClick = (site) => {
    setSelectedEspace(site);
    setIsEditModalOpen(true);
  };

  const getCouleurSante = (score) => {
    if (typeof score !== "number") return "#64748B";
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
          <h1 className="text-3xl font-bold text-fg tracking-tight">Espaces et zones</h1>
          <p className="text-fg-muted mt-1">Vos espaces verts regroupés par zone géographique</p>
          {recalcul.message && <p role="status" className="text-sm text-fg-soft mt-2">{recalcul.message}</p>}
        </div>
        {peutGerer && <div className="flex gap-3">
        <button
          type="button"
          onClick={recalculerZones}
          disabled={recalcul.enCours || espaces.length === 0}
          className="hidden md:flex items-center gap-2 bg-surface-raised hover:bg-surface-strong disabled:opacity-50 text-fg px-5 py-2 rounded-xl font-bold transition-all"
        >
          <Layers size={18} aria-hidden />
          <span>{recalcul.enCours ? "Calcul…" : "Recalculer les zones"}</span>
        </button>

        <button 
          onClick={() => setIsAddModalOpen(true)}
          className="hidden md:flex items-center gap-2 bg-primary hover:bg-primary-hover text-on-accent px-5 py-2 rounded-xl font-bold transition-all shadow-lg"
        >
          <Plus size={20} />
          <span>Ajouter un espace</span>
        </button>
        </div>}
      </div>

      {/* SECTION DES JAUGES DE CLUSTERS (inchangée) ... */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <button
          type="button"
          aria-pressed={!activeClusterId}
          onClick={() => setActiveClusterId(null)}
          className={`text-left p-4 rounded-2xl border transition-all ${
            !activeClusterId ? "bg-surface-raised border-success shadow-lg" : "bg-surface border-line hover:border-line-strong"
          }`}
        >
          <div className="flex justify-between items-center">
             <span className="text-xs font-bold text-fg-muted uppercase">Vue Globale</span>
             <Layers size={16} className={!activeClusterId ? "text-success" : "text-fg-subtle"} />
          </div>
          <p className="text-2xl font-black text-fg mt-2">{espaces.length}</p>
        </button>

        {clusters.map((cluster) => {
          const couleur = getCouleurSante(cluster.sante_moyenne);
          const isActive = activeClusterId === cluster.id;
          return (
            <button
              type="button"
              key={cluster.id}
              aria-pressed={isActive}
              onClick={() => setActiveClusterId(cluster.id)}
              className={`text-left p-4 rounded-2xl border transition-all relative overflow-hidden ${
                isActive ? "bg-surface-raised border-white/20 shadow-xl scale-[1.02]" : "bg-surface border-line hover:border-line-strong"
              }`}
            >
              <div className="flex justify-between items-start relative z-10">
                <div className="max-w-[70%]">
                  <span className="text-xs font-bold text-fg-muted uppercase truncate block">{cluster.nom}</span>
                  <p className="text-2xl font-black text-fg mt-1">{cluster.nb_espaces}</p>
                </div>
                <div className="relative w-12 h-12 flex items-center justify-center">
                   <svg className="w-full h-full transform -rotate-90">
                      <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4" fill="transparent" className="text-fg-subtle" />
                      <circle 
                        cx="24" cy="24" r="20" stroke={couleur} strokeWidth="4" fill="transparent" 
                        strokeDasharray={125}
                        strokeDashoffset={125 - (125 * (cluster.sante_moyenne ?? 0)) / 100}
                        strokeLinecap="round"
                      />
                   </svg>
                   <span className="absolute text-xs font-bold text-fg">{typeof cluster.sante_moyenne === "number" ? `${Math.round(cluster.sante_moyenne)}%` : "–"}</span>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* BARRE DE RECHERCHE  ... */}
      <div className="flex flex-col md:flex-row gap-4 items-center bg-surface/50 p-4 rounded-2xl border border-line">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-fg-muted" size={18} />
          <input 
            type="search"
            aria-label="Rechercher un espace par nom"
            placeholder="Rechercher par nom…"
            className="w-full bg-canvas border border-line rounded-xl py-3 pl-12 pr-4 text-fg outline-none focus:ring-1 focus:ring-focus"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex bg-canvas p-1 rounded-lg border border-line">
          <button type="button" aria-label="Affichage en grille" aria-pressed={viewMode === "grid"} onClick={() => setViewMode("grid")} className={`p-2 rounded ${viewMode === "grid" ? "bg-surface-raised text-fg" : "text-fg-muted"}`}><LayoutGrid size={18} /></button>
          <button type="button" aria-label="Affichage en liste" aria-pressed={viewMode === "list"} onClick={() => setViewMode("list")} className={`p-2 rounded ${viewMode === "list" ? "bg-surface-raised text-fg" : "text-fg-muted"}`}><List size={18} /></button>
        </div>
      </div>

      {loading && <p role="status" className="text-fg-muted text-sm">Chargement des espaces…</p>}
      {!loading && espaces.length === 0 && (
        <p className="text-fg-muted text-sm">
          {peutGerer ? "Aucun espace vert pour le moment : ajoutez votre premier site." : "Aucun espace vert pour le moment."}
        </p>
      )}

      {/* LISTE DES SITES */}
      <div className={viewMode === "grid" ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" : "space-y-4"}>
        {sitesFiltres.map((site) => {
          const contenu = (
            <>
            <h3 className="text-xl font-bold text-fg mb-1">{site.nom}</h3>
            <div className="flex items-center gap-2 text-fg-muted text-sm mb-4">
              <MapPin size={14} />
              <span>{site.ville}</span>
            </div>
            <div className="pt-4 border-t border-line flex justify-between items-center text-xs text-fg-muted font-bold uppercase">
               <span>Zone : {nomZone(site.zone_id)}</span>
               <span className={site.sante_percent >= 85 ? "text-success" : "text-warning"}>
                 {typeof site.sante_percent === "number" ? `${Math.round(site.sante_percent)} % santé` : "Santé : en attente"}
               </span>
            </div>
            </>
          );
          // Carte cliquable (modale d'édition) uniquement pour les rôles de gestion
          return peutGerer ? (
            <button
              type="button"
              key={site.id}
              onClick={() => handleEditClick(site)}
              aria-label={`Modifier ${site.nom}`}
              className="text-left w-full bg-surface border border-line rounded-2xl p-5 hover:border-success/50 transition-all group cursor-pointer"
            >
              {contenu}
            </button>
          ) : (
            <article key={site.id} className="w-full bg-surface border border-line rounded-2xl p-5">
              {contenu}
            </article>
          );
        })}
      </div>

      {/* BOUTON MOBILE FLOTTANT (FAB) */}
      {peutGerer && <button
        type="button"
        onClick={() => setIsAddModalOpen(true)}
        aria-label="Ajouter un espace"
        className="md:hidden fixed bottom-6 right-6 z-50 rounded-full bg-primary p-4 text-on-accent shadow-2xl"
      >
        {/* Halo d'invitation quand la liste est vide (désactivé si « réduire les animations ») */}
        {aBesoinDePulse && <span aria-hidden className="absolute inset-0 rounded-full bg-primary/40 animate-ping" />}
        <Plus size={28} aria-hidden className="relative" />
      </button>}

      {/* MODALES */}
      {peutGerer && isAddModalOpen && (
        <AddSpaceModal 
          onClose={() => setIsAddModalOpen(false)} 
          onSuccess={chargerDonnees} 
        />
      )}
      
      {/* 4. Rendu conditionnel de la modale d'édition */}
      {peutGerer && isEditModalOpen && selectedEspace && (
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