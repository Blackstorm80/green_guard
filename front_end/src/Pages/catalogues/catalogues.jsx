import { useState, useEffect, useMemo } from "react";
import { api } from "../../services/api";
import { useTitrePage } from "../../lib/hooks";
import { Button } from "../../components/ui/Button";

const TAILLE_PAGE = 40;
import { Search, Leaf, Bug, Droplets, Thermometer, Info, AlertCircle } from "lucide-react";

export default function Catalogues() {
  useTitrePage("Catalogue");
  const [data, setData] = useState({ plantes: [], auxiliaires: [] });
  const [activeTab, setActiveTab] = useState("plantes");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 1. Chargement des données
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

  // 2. Le Cœur : Algorithme de filtrage "Multi-Modèle"
  const [limite, setLimite] = useState(TAILLE_PAGE);
  // Nouvelle recherche ou nouvel onglet : on repart de la première page
  const [cleFiltre, setCleFiltre] = useState("");
  if (cleFiltre !== `${activeTab}|${searchTerm}`) {
    setCleFiltre(`${activeTab}|${searchTerm}`);
    setLimite(TAILLE_PAGE);
  }

  const resultats = useMemo(() => {
    const source = activeTab === "plantes" ? data.plantes : data.auxiliaires;
    
    const filtered = source.filter(item => {
      // Pont logique entre les clés "plantes" et "auxiliaires"
      const mainName = (item.nom_commun || item.nom || "").toLowerCase();
      const secondaryName = (item.nom_scientifique || item.role || "").toLowerCase();
      const search = searchTerm.toLowerCase();

      return mainName.includes(search) || secondaryName.includes(search);
    });

    return filtered;
  }, [searchTerm, activeTab, data]);
  // Affichage par pages : rendre 1 258 cartes d'un coup ralentirait la page
  const filteredItems = resultats.slice(0, limite);

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-fg-muted gap-4">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-success"></div>
      <p className="font-medium animate-pulse">Extraction du savoir botanique...</p>
    </div>
  );

  if (error) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-danger gap-4">
      <AlertCircle size={48} />
      <p>{error}</p>
    </div>
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-fg">Catalogue botanique</h1>
        <p className="mt-1 text-fg-muted">Plantes et insectes auxiliaires issus des observations iNaturalist.</p>
      </div>

      {/* --- BARRE D'OUTILS --- */}
      <div className="flex flex-col xl:flex-row gap-6 justify-between items-center bg-surface/40 p-5 rounded-[2rem] border border-line/50 backdrop-blur-md">
        
        <div role="tablist" aria-label="Type de fiche" className="flex bg-canvas p-1.5 rounded-2xl border border-line shadow-inner">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "plantes"}
            onClick={() => setActiveTab("plantes")}
            className={`px-8 py-3 rounded-xl flex items-center gap-3 font-bold transition-all duration-300 ${
              activeTab === "plantes" ? "bg-primary text-on-accent shadow-lg shadow-green-900/40 scale-105" : "text-fg-muted hover:text-fg"
            }`}
          >
            <Leaf size={20} /> Plantes <span className="text-xs opacity-60 ml-2">{data.plantes.length}</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "auxiliaires"}
            onClick={() => setActiveTab("auxiliaires")}
            className={`px-8 py-3 rounded-xl flex items-center gap-3 font-bold transition-all duration-300 ${
              activeTab === "auxiliaires" ? "bg-blue-600 text-on-accent shadow-lg shadow-blue-900/40 scale-105" : "text-fg-muted hover:text-fg"
            }`}
          >
            <Bug size={20} /> Auxiliaires <span className="text-xs opacity-60 ml-2">{data.auxiliaires.length}</span>
          </button>
        </div>

        <div className="relative w-full max-w-2xl group">
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-fg-muted group-focus-within:text-success transition-colors" size={22} />
          <input 
            type="search"
            aria-label={activeTab === "plantes" ? "Rechercher une plante" : "Rechercher un auxiliaire"}
            placeholder={activeTab === "plantes" ? "Rechercher une plante…" : "Rechercher un auxiliaire…"}
            className="w-full bg-canvas/80 border border-line rounded-3xl py-5 pl-14 pr-6 text-fg focus:ring-2 focus:ring-focus/50 outline-none transition-all placeholder:text-fg-subtle shadow-lg"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <p className="text-sm text-fg-muted" aria-live="polite">
        {resultats.length
          ? `${filteredItems.length} affichée(s) sur ${resultats.length} fiche(s)`
          : null}
      </p>

      {/* --- GRILLE DE CARTES --- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
        {filteredItems.map((item) => (
          <div key={item.id} className="group relative bg-surface/30 border border-line/60 rounded-[2.5rem] p-5 hover:border-success/40 hover:bg-surface/50 transition-all duration-500">
            
            <div className="aspect-[4/3] rounded-[2rem] overflow-hidden bg-canvas mb-6 relative">
              <ImageFiche url={item.url_image} alt={item.nom_commun || item.nom} />
              <div className="absolute top-4 right-4 bg-canvas/60 backdrop-blur-md p-2 rounded-full text-fg/50 opacity-0 group-hover:opacity-100 transition-opacity">
                <Info size={16} />
              </div>
            </div>

            <div className="px-2 space-y-3">
              <div>
                <h3 className="text-fg text-xl font-black truncate group-hover:text-success transition-colors capitalize">
                  {/* Utilisation de la clé universelle */}
                  {item.nom_commun || item.nom}
                </h3>
                <p className="text-fg-muted text-sm font-medium truncate">
                  {/* Utilisation de la clé universelle */}
                  {item.nom_scientifique || item.role}
                </p>
              </div>
              
              {activeTab === "plantes" && (
                <div className="flex justify-between items-center pt-5 mt-2 border-t border-line/40">
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-info-soft rounded-full text-info border border-blue-500/10">
                    <Droplets size={14} aria-hidden />
                    <span className="text-xs font-black">{item.besoin_eau ?? "Eau : non renseigné"}</span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-success-soft rounded-full text-success border border-emerald-500/10">
                    <Thermometer size={14} />
                    <span className="text-xs font-black">{item.ph_ideal != null ? `pH ${item.ph_ideal}` : "pH : non renseigné"}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredItems.length < resultats.length && (
        <div className="flex justify-center">
          <Button variante="secondaire" onClick={() => setLimite((l) => l + TAILLE_PAGE)}>
            Afficher {Math.min(TAILLE_PAGE, resultats.length - filteredItems.length)} fiche(s) de plus
          </Button>
        </div>
      )}

      {/* État vide */}
      {filteredItems.length === 0 && (
        <div className="flex flex-col items-center justify-center py-32 space-y-4 bg-surface/20 rounded-[3rem] border border-dashed border-line">
          <Search size={64} className="text-fg-subtle" />
          <div className="text-center">
            <p className="text-fg-muted text-lg font-bold">Aucune fiche trouvée</p>
            <p className="text-fg-muted text-sm">Essayez un autre mot-clé.</p>
          </div>
        </div>
      )}
    </div>
  );
}

/** Photo de la fiche, ou pictogramme local si elle est absente ou introuvable. */
function ImageFiche({ url, alt }) {
  const [enErreur, setEnErreur] = useState(false);
  if (!url || enErreur) {
    return (
      <div role="img" aria-label="Pas de photo disponible" className="flex h-full w-full items-center justify-center text-fg-subtle">
        <Leaf size={48} aria-hidden />
      </div>
    );
  }
  return (
    <img
      src={url}
      alt={alt}
      loading="lazy"
      onError={() => setEnErreur(true)}
      className="h-full w-full object-cover opacity-90 transition-all duration-700 group-hover:scale-105 group-hover:opacity-100"
    />
  );
}
