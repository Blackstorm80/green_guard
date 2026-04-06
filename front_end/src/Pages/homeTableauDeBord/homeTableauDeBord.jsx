import { useState, useEffect } from "react";
import { 
  Activity, CheckCircle, AlertTriangle, Thermometer, 
  Droplets, Wind, ChevronDown, ChevronUp, Sun, Gauge, 
  Clock, ShieldAlert, Flame, Wrench, Cpu, Zap 
} from "lucide-react";
import { api } from "../../services/api";

export default function HomeTableauDeBord() {
  const [diagnostic, setDiagnostic] = useState(null);
  const [espaces, setEspaces] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [afficherPlus, setAfficherPlus] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    initialiserDashboard();
    const interval = setInterval(initialiserDashboard, 30000);
    return () => clearInterval(interval);
  }, []);

  const initialiserDashboard = async () => {
    try {
      // Appel unifié pour récupérer l'ensemble des données du tableau de bord.
      // L'API retourne maintenant un objet contenant le statut global et la liste des noeuds.
      const stats = await api.getDashboardStats(); // On suppose que cet appel ne nécessite plus d'IDs.

      // On vérifie que la réponse contient bien un tableau de capteurs/espaces.
      if (stats && Array.isArray(stats.capteurs) && stats.capteurs.length > 0) {
        // 'stats.capteurs' est la nouvelle source de vérité pour la liste des espaces.
        setEspaces(stats.capteurs);
        // 'diagnostic' contient l'objet complet avec le statut global, message, etc.
        setDiagnostic(stats);
        console.log("DATA_TELEMETRIE_ACTIVE :", stats);
      } else {
        // Si aucune donnée n'est retournée ou si le tableau est vide, on initialise avec un état vide.
        setEspaces([]);
        setDiagnostic({ statut: "Vide", message: "Aucun noeud détecté dans la flotte." });
      }

      setLastUpdate(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      console.error("ERREUR_SYNCHRO_TACTIQUE :", err);
      setError("Rupture de liaison avec le centre de données.");
      setEspaces([]); // Important: en cas d'erreur, garantir que 'espaces' reste un tableau.
    } finally {
      setLoading(false);
    }
  };

  const executerActionRapide = async (id, action) => {
    setIsProcessing(true);
    try {
      // Appel réel vers ton futur orchestrateur d'actions
      await api.triggerAction({ espace_id: id, type: action });
      await initialiserDashboard();
    } catch (err) {
      console.error("ECHEC_INTERVENTION :", err);
    } finally {
      setIsProcessing(false);
    }
  };

  if (loading && !diagnostic) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <div className="w-10 h-10 border-2 border-green-500/20 border-t-green-500 rounded-full animate-spin"></div>
        <p className="text-[10px] font-mono text-green-500 uppercase tracking-[0.3em]">Sync_Bio_Kernel...</p>
      </div>
    );
  }

  const isSain = diagnostic?.statut === "Sain";
  
  // Calcul du KPI de santé (Moyenne de la flotte)
  const santeGlobale = espaces.length > 0 
    ? Math.round(espaces.reduce((acc, curr) => acc + (curr.sante_percent || 0), 0) / espaces.length)
    : 0;

  const sitesEnAlerte = espaces.filter(e => (e.sante_percent || 100) < 70);

  return (
    <div className="space-y-6 font-mono text-slate-300 animate-in fade-in duration-700">
      
      {/* BARRE DE STATUT SYSTÈME */}
      <div className="flex justify-between items-center bg-slate-900/50 border border-slate-800 p-3 rounded-lg text-[10px] font-black uppercase tracking-widest">
        <div className="flex gap-6">
          <div className="flex items-center gap-2"><Cpu size={14} className="text-green-500"/> Nodes_Active: {espaces.length}</div>
          <div className="flex items-center gap-2 text-blue-400"><Zap size={14}/> Live_Telemetry</div>
        </div>
        <div className="flex items-center gap-2 text-white bg-slate-800 px-3 py-1 rounded border border-slate-700">
          <Clock size={12} /> {lastUpdate}
        </div>
      </div>

      {/* KPI GLOBAL & ÉTAT UNITÉ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 p-6 rounded-2xl border-2 transition-all bg-slate-900 border-slate-800 relative overflow-hidden">
          <div className="flex items-center gap-6 relative z-10">
            <div className={`p-4 rounded-xl ${isSain ? "bg-green-500 text-slate-950" : "bg-amber-500 text-slate-950"}`}>
              {isSain ? <CheckCircle size={32} /> : <AlertTriangle size={32} />}
            </div>
            <div>
              <h2 className="text-3xl font-black text-white tracking-tighter uppercase italic">{diagnostic?.statut}</h2>
              <p className="text-slate-500 text-xs mt-1">{diagnostic?.message}</p>
            </div>
          </div>
          <Activity size={100} className="absolute -right-4 -bottom-4 text-slate-800/20" />
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col justify-center text-center">
          <span className="text-[10px] text-slate-500 font-black uppercase mb-2">Fleet_Integrity</span>
          <span className="text-5xl font-black text-white italic">{santeGlobale}%</span>
          <div className="w-full bg-slate-800 h-1.5 mt-4 rounded-full overflow-hidden">
            <div className="bg-green-500 h-full transition-all duration-1000" style={{ width: `${santeGlobale}%` }}></div>
          </div>
        </div>
      </div>

      {/* MATRICE D'INTERVENTION TACTIQUE */}
      {sitesEnAlerte.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-rose-500 text-[10px] font-black uppercase tracking-widest">
            <ShieldAlert size={16} /> Interventions_Requises
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sitesEnAlerte.map(site => (
              <ActionCard key={site.id} site={site} onAction={executerActionRapide} disabled={isProcessing} />
            ))}
          </div>
        </section>
      )}

      {/* GRILLE DE TÉLÉMÉTRIE PRINCIPALE */}
      <div className="space-y-8">
        {(diagnostic?.capteurs || []).map((capteur, index) => (
          <div key={capteur.espace_id || index}>
            <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-3">Telemetry_Node_{capteur.espace_id || index}</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard icon={<Thermometer className="text-orange-400" />} label="Temp_Core" value={capteur.temperature_c} unit="°C" />
              <MetricCard icon={<Wind className="text-blue-400" />} label="O2_Level" value={capteur.o2_percent} unit="%" />
              <MetricCard icon={<Droplets className="text-teal-400" />} label="Soil_Sat" value={capteur.humidite_percent} unit="%" />
              <MetricCard icon={<Activity className="text-purple-400" />} label="CO2_Level" value={capteur.co2_ppm} unit="ppm" />
            </div>

            {/* PARAMÈTRES AVANCÉS */}
            <div className="flex flex-col items-center mt-4">
              <button 
                onClick={() => setAfficherPlus(!afficherPlus)}
                className="group flex items-center gap-2 px-6 py-2 bg-slate-900 hover:bg-slate-800 text-[10px] font-black uppercase tracking-[0.2em] rounded-full border border-slate-700 transition-all shadow-xl"
              >
                {afficherPlus ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {afficherPlus ? "Close_Buffer" : "Open_Extended_Data"}
              </button>

              {afficherPlus && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full mt-6 animate-in slide-in-from-top-4 duration-300">
                  <MetricCard icon={<Sun className="text-yellow-400" />} label="Lux_Index" value={capteur.luminosite_lux} unit="lx" isSmall />
                  <MetricCard icon={<Droplets className="text-indigo-400" />} label="Res_Eau" value={capteur.reserve_eau_mm} unit="mm" isSmall />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ActionCard({ site, onAction, disabled }) {
  const needsWater = site.humidite_sol < 40;
  return (
    <div className="bg-slate-900/80 border-l-4 border-l-rose-500 border border-slate-800 p-4 rounded-lg">
      <div className="flex justify-between items-center mb-3">
        <span className="text-[10px] font-black text-white truncate w-2/3">{site.nom}</span>
        <span className="text-[9px] font-bold text-rose-500">{site.sante_percent}% HP</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button onClick={() => onAction(site.id, 'water')} disabled={disabled} className="bg-blue-600 hover:bg-blue-500 text-[9px] font-black py-2 rounded uppercase text-white transition-all">Water</button>
        <button onClick={() => onAction(site.id, 'heat')} disabled={disabled} className="bg-orange-600 hover:bg-orange-500 text-[9px] font-black py-2 rounded uppercase text-white transition-all">Heat</button>
        <button onClick={() => onAction(site.id, 'cover')} disabled={disabled} className="bg-slate-700 hover:bg-slate-600 text-[9px] font-black py-2 rounded uppercase text-white transition-all">Cover</button>
        <button onClick={() => onAction(site.id, 'repair')} disabled={disabled} className="bg-slate-800 hover:bg-slate-700 text-[9px] font-black py-2 rounded uppercase text-slate-400 transition-all flex items-center justify-center gap-1"><Wrench size={10}/> Expert</button>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, unit, isSmall = false }) {
  return (
    <div className={`bg-slate-950/50 p-4 rounded-xl border border-slate-800 flex items-center gap-4 group hover:border-slate-500 transition-all ${isSmall ? 'opacity-70' : ''}`}>
      <div className="p-3 bg-slate-900 rounded-lg group-hover:scale-110 transition-transform">{icon}</div>
      <div>
        <p className="text-[8px] text-slate-500 font-black uppercase tracking-widest">{label}</p>
        <div className="flex items-baseline gap-1">
          <p className="text-xl font-black text-white italic">{value ?? "--"}</p>
          <span className="text-[10px] text-slate-600 font-bold">{unit}</span>
        </div>
      </div>
    </div>
  );
}