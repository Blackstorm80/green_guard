// front_end/src/Pages/espacesEtSites/espaceEtSites.jsx
import React, { useState, useMemo, useEffect } from 'react';
import { Search, LayoutGrid, List } from 'lucide-react';
import { api } from '../../services/api';

// ============================================================================
// Fonctions Utilitaires et Composants de Présentation
// ============================================================================

const getHealthColor = (health) => {
  if (health >= 85) return '#0CB95D'; // Vert
  if (health >= 65) return '#E77C02'; // Orange
  return '#DF1B1B'; // Rouge
};

const RadialGauge = ({ health }) => {
  const safeHealth = Math.max(0, Math.min(100, health || 0));
  const color = getHealthColor(safeHealth);
  const radius = 35;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (safeHealth / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center">
      <svg className="transform -rotate-90 w-24 h-24">
        <circle cx="48" cy="48" r={radius} stroke="#374151" strokeWidth="8" fill="transparent" />
        <circle
          cx="48"
          cy="48"
          r={radius}
          stroke={color}
          strokeWidth="8"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.5s ease-in-out, stroke 0.5s ease' }}
        />
      </svg>
      <span className="absolute text-xl font-bold text-white">{Math.round(safeHealth)}%</span>
    </div>
  );
};

const ClusterWidget = ({ cluster, isActive, onClick }) => {
  const activeClasses = isActive ? 'border-teal-400 shadow-xl shadow-teal-400/20' : 'border-slate-800';

  return (
    <div
      onClick={onClick}
      className={`flex flex-col items-center justify-center p-4 bg-gray-900 border ${activeClasses} rounded-lg cursor-pointer transition-all duration-500 h-full`}
    >
      <RadialGauge health={cluster.sante_moyenne} />
      <p className="mt-2 text-sm font-semibold text-white text-center">{cluster.nom}</p>
      <p className="text-xs text-slate-400">Santé Moyenne</p>
    </div>
  );
};

const SpaceCard = ({ space }) => {
    const healthColor = getHealthColor(space.sante_percent);
    return (
      <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4 flex items-center relative overflow-hidden transition-all duration-500 hover:bg-slate-800/60">
        <div className="absolute left-0 top-0 bottom-0 w-1" style={{ backgroundColor: healthColor }}></div>
        <div className="ml-4 flex-grow">
          <p className="font-bold text-white">{space.nom}</p>
          <p className="text-sm text-slate-500">{space.ville || 'Localisation non définie'}</p>
        </div>
        <div className="flex items-center">
          <span className="text-white font-semibold">{Math.round(space.sante_percent)}%</span>
          <div className="w-2 h-2 rounded-full ml-2" style={{ backgroundColor: healthColor }}></div>
        </div>
      </div>
    );
};

// ============================================================================
// Composant Principal: EspacesEtSites
// ============================================================================

const EspacesEtSites = () => {
    // --- États ---
    const [spaces, setSpaces] = useState([]);
    const [clusters, setClusters] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [viewMode, setViewMode] = useState('grid');
    const [activeCluster, setActiveCluster] = useState(null);
    const [isSearchFocused, setIsSearchFocused] = useState(false);
    const [error, setError] = useState(null);

    // --- Récupération des données ---
    useEffect(() => {
        const fetchData = async () => {
            try {
                // Règle de Synchronisation: Appels couplés pour garantir l'intégrité.
                const [spacesData, zonesData] = await Promise.all([
                    api.getEspacesVerts(),
                    api.getZones()
                ]);

                if (Array.isArray(zonesData) && zonesData.length > 0) {
                     // NOTE: Le backend ne renvoie pas le lien entre un espace et sa zone.
                    // En l'absence de `zone_id` sur l'objet `EspaceVert`, nous simulons
                    // l'appartenance à un cluster pour faire fonctionner le filtrage de l'UI.
                    // La logique ci-dessous doit être remplacée quand l'API renverra ce lien.
                    const spacesWithCluster = spacesData.map((space, index) => ({
                        ...space,
                        clusterId: zonesData[index % zonesData.length].id
                    }));
                    setSpaces(spacesWithCluster);
                } else {
                    setSpaces(spacesData);
                }
               
                setClusters(zonesData);

            } catch (err) {
                console.error("Erreur lors de la récupération des données:", err);
                setError("Impossible de charger les données. Vérifiez la connexion avec le backend.");
            }
        };
        fetchData();
    }, []);

    // --- Logique de filtrage ---
    const filteredSpaces = useMemo(() => {
        if (!Array.isArray(spaces)) return [];
        return spaces.filter(space => {
            const matchesCluster = activeCluster ? space.clusterId === activeCluster : true;
            const matchesSearch = space.nom.toLowerCase().includes(searchTerm.toLowerCase());
            return matchesCluster && matchesSearch;
        });
    }, [searchTerm, activeCluster, spaces]);

    if (error) {
        return <div className="flex items-center justify-center h-screen bg-gray-900 text-red-500">{error}</div>;
    }

    return (
        <div className="bg-gray-900 min-h-screen p-8 text-white">
            <h1 className="text-3xl font-bold mb-6">Espaces & Sites</h1>

            {/* Niveau 1: Clusters Intelligents */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
                <div
                    onClick={() => setActiveCluster(null)}
                    className={`flex flex-col items-center justify-center p-4 border rounded-lg cursor-pointer transition-all duration-500 ${!activeCluster ? 'bg-teal-600 border-teal-400 shadow-lg' : 'bg-gray-800 border-slate-700 hover:bg-gray-700'}`}
                >
                    <p className="text-3xl font-bold">{spaces.length}</p>
                    <p className="mt-1 font-bold">Global</p>
                </div>
                <div className="md:col-span-4 grid grid-cols-1 md:grid-cols-4 gap-4">
                    {Array.isArray(clusters) && clusters.map(cluster => (
                        <ClusterWidget
                            key={cluster.id}
                            cluster={cluster}
                            isActive={activeCluster === cluster.id}
                            onClick={() => setActiveCluster(cluster.id)}
                        />
                    ))}
                </div>
            </div>

            {/* Niveau 2: Barre de Filtrage */}
            <div className="sticky top-4 z-10 mb-8">
                <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800 rounded-lg p-2 flex items-center justify-between gap-4">
                    <div className="relative flex-grow">
                        <Search className={`absolute left-3 top-1/2 -translate-y-1/2 transition-colors duration-300 ${isSearchFocused ? 'text-teal-400' : 'text-slate-500'}`} size={20} />
                        <input
                            type="text"
                            placeholder={`Rechercher parmi ${filteredSpaces.length} sites...`}
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            onFocus={() => setIsSearchFocused(true)}
                            onBlur={() => setIsSearchFocused(false)}
                            className="w-full bg-transparent pl-10 pr-4 py-2 text-white rounded-md focus:outline-none"
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <button onClick={() => setViewMode('grid')} className={`p-2 rounded-md transition-colors duration-300 ${viewMode === 'grid' ? 'bg-teal-500/20 text-teal-400' : 'text-slate-500 hover:bg-slate-700/50'}`}>
                            <LayoutGrid size={20} />
                        </button>
                        <button onClick={() => setViewMode('list')} className={`p-2 rounded-md transition-colors duration-300 ${viewMode === 'list' ? 'bg-teal-500/20 text-teal-400' : 'text-slate-500 hover:bg-slate-700/50'}`}>
                            <List size={20} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Niveau 3: Liste des Espaces */}
            <div className={`transition-all duration-500 ${viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6' : 'flex flex-col gap-4'}`}>
                {Array.isArray(filteredSpaces) && filteredSpaces.map(space => (
                    <SpaceCard key={space.id} space={space} />
                ))}
            </div>
            {filteredSpaces.length === 0 && !error && (
                <div className="text-center py-12 text-slate-500">
                    <p>Aucun espace ne correspond à votre recherche.</p>
                </div>
            )}
        </div>
    );
};

export default EspacesEtSites;
