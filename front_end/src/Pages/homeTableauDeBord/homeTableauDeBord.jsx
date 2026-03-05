import { useState, useEffect } from "react";
import { 
  Activity, 
  CheckCircle, 
  AlertTriangle, 
  Thermometer, 
  Droplets, 
  Wind, 
  ChevronDown, 
  ChevronUp, 
  Sun, 
  Gauge,
  Clock
} from "lucide-react";
import { api } from "../../services/api";

export default function HomeTableauDeBord() {
  const [diagnostic, setDiagnostic] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [afficherPlus, setAfficherPlus] = useState(false);

  useEffect(() => {
    chargerDonnees();
    // Rafraichissement automatique toutes les 30 secondes pour le "vrai" temps reel
    const interval = setInterval(chargerDonnees, 30000);
    return () => clearInterval(interval);
  }, []);

  const chargerDonnees = async () => {
    try {
      const data = await api.getDashboardStats();
      setDiagnostic(data);
      setLastUpdate(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      setError("Erreur de synchronisation reseau.");
    } finally {
      setLoading(false);
    }
  };

  if (loading && !diagnostic) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const isSain = diagnostic?.statut === "Sain";
  const m = diagnostic?.mesures || {};

  return (
    <div className="space-y-6 animate-in fade-in duration-700">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-white">Tableau de Bord</h1>
          <p className="text-slate-400 text-sm">Surveillance active des capteurs</p>
        </div>
        {lastUpdate && (
          <div className="flex items-center gap-2 text-[10px] text-slate-500 uppercase font-bold tracking-wider bg-slate-800/50 px-3 py-1 rounded-full">
            <Clock size={12} />
            MAJ: {lastUpdate}
          </div>
        )}
      </div>

      <div className={`relative p-6 rounded-2xl border transition-all duration-500 ${
        isSain ? "bg-emerald-900/10 border-emerald-500/20" : "bg-amber-900/10 border-amber-500/20"
      }`}>
        
        <div className="flex items-center gap-5 mb-10">
          <div className={`p-4 rounded-2xl shadow-lg ${isSain ? "bg-emerald-500 text-slate-950" : "bg-amber-500 text-slate-950"}`}>
            {isSain ? <CheckCircle size={32} strokeWidth={2.5} /> : <AlertTriangle size={32} strokeWidth={2.5} />}
          </div>
          <div>
            <h2 className="text-4xl font-black text-white tracking-tight">
              {diagnostic?.statut}
            </h2>
            <p className="text-slate-400 font-medium">{diagnostic?.message}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard icon={<Thermometer className="text-orange-400" />} label="Temperature" value={`${m.temperature ?? "--"}°C`} />
          <MetricCard icon={<Wind className="text-blue-400" />} label="Humidite Air" value={`${m.humidite_rel ?? "--"}%`} />
          <MetricCard icon={<Droplets className="text-teal-400" />} label="Humidite Sol" value={`${m.humidite_sol ?? "--"}%`} />
          <MetricCard icon={<Activity className="text-purple-400" />} label="CO2" value={`${m.co2 ?? "--"} ppm`} />
        </div>

        <div className="flex justify-center -mb-9 mt-8">
          <button 
            onClick={() => setAfficherPlus(!afficherPlus)}
            className="group flex items-center gap-2 px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-full text-xs font-bold uppercase tracking-widest transition-all border border-slate-700 shadow-2xl"
          >
            {afficherPlus ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {afficherPlus ? "Moins de details" : "Plus de parametres"}
          </button>
        </div>

        {afficherPlus && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-12 pt-10 border-t border-slate-800/50 animate-in slide-in-from-top-4 duration-500">
            <MetricCard icon={<Sun className="text-yellow-400" />} label="Luminosite" value={`${m.luminosite ?? "--"} lx`} isSmall />
            <MetricCard icon={<Gauge className="text-indigo-400" />} label="Pression" value={`${m.pression_atm ?? "--"} hPa`} isSmall />
          </div>
        )}
      </div>
    </div>
  );
}

// Sous-composant pour la proprete du code (Le Coeur de l'interface)
function MetricCard({ icon, label, value, isSmall = false }) {
  return (
    <div className={`bg-slate-950/40 p-4 rounded-xl border border-slate-800/50 flex items-center gap-4 hover:border-slate-600 transition-colors ${isSmall ? "opacity-80" : ""}`}>
      <div className="p-2 bg-slate-900 rounded-lg">{icon}</div>
      <div>
        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">{label}</p>
        <p className="text-xl font-bold text-white tracking-tight">{value}</p>
      </div>
    </div>
  );
}