import { useState, useEffect } from "react";
import { 
  Activity, CheckCircle, AlertTriangle, Thermometer, 
  Droplets, Wind, ChevronDown, ChevronUp, Sun, Cpu, Zap, 
  Clock, ShieldAlert, Wrench, Target
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
      const stats = await api.getDashboardStats(); 

      if (stats && Array.isArray(stats.capteurs) && stats.capteurs.length > 0) {
        setEspaces(stats.capteurs);
        setDiagnostic(stats);
      } else {
        setEspaces([]);
        setDiagnostic({ statut: "En attente", message: "Aucune donnée télémétrique reçue." });
      }

      setLastUpdate(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      console.error("ERREUR_SYNCHRO_TACTIQUE :", err);
      setError("Rupture de liaison avec le centre de données.");
      setEspaces([]);
    } finally {
      setLoading(false);
    }
  };

  const executerActionRapide = async (id, action) => {
    setIsProcessing(true);
    try {
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

  // --- SÉCURITÉ & CALCULS DES KPIs ---
  const isSain = diagnostic?.statut === "Sain";
  
  const validHealthNodes = espaces.filter(e => typeof e.sante_percent === 'number');
  const santeGlobale = validHealthNodes.length > 0 
    ? Math.round(validHealthNodes.reduce((acc, curr) => acc + curr.sante_percent, 0) / validHealthNodes.length)
    : "--"; 

  const sitesEnAlerte = espaces.filter(e => {
    const sante = typeof e.sante_percent === 'number' ? e.sante_percent : 100;
    return sante < 70;
  });

  // Nouveaux KPIs Globaux (Zéro-Hardcode, basés sur le tableau espaces)
  const saturationGlobale = espaces.length > 0 
    ? Math.round(espaces.reduce((acc, curr) => acc + (curr.humidite_percent || 0), 0) / espaces.length) 
    : "--";

  const co2Moyen = espaces.length > 0 
    ? Math.round(espaces.reduce((acc, curr) => acc + (curr.co2_ppm || 0), 0) / espaces.length) 
    : "--";

  const noeudsEnStressThermique = espaces.filter(e => 
    typeof e.temperature_c === 'number' && (e.temperature_c < 15 || e.temperature_c > 30)
  ).length;

  return (
    <div className="space-y-6 font-mono text-slate-300 animate-in fade-in duration-700">
      
      {/* BARRE DE STATUT SYSTÈME */}
      <div className="flex justify-between items-center bg-slate-900/50 border border-slate-800 p-3 rounded-lg text-[10px] font-black uppercase tracking-widest">
        <div className="flex gap-6">
          <div className="flex items-center gap-2"><Cpu size={14} className="text-green-500"/> Nodes_Active: {espaces.length}</div>
          <div className="flex items-center gap-2 text-blue-400"><Zap size={14}/> Live_Telemetry</div>
        </div>
        <div className="flex items-center gap-2 text-white bg-slate-800 px-3 py-1 rounded border border-slate-700">
          <Clock size={12} /> {lastUpdate || "--:--:--"}
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg text-xs font-bold flex items-center gap-2">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* KPI GLOBAL & ÉTAT UNITÉ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 p-6 rounded-2xl border-2 transition-all bg-slate-900 border-slate-800 relative overflow-hidden">
          <div className="flex items-center gap-6 relative z-10">
            <div className={`p-4 rounded-xl ${isSain ? "bg-green-500 text-slate-950" : "bg-amber-500 text-slate-950"}`}>
              {isSain ? <CheckCircle size={32} /> : <AlertTriangle size={32} />}
            </div>
            <div>
              <h2 className="text-3xl font-black text-white tracking-tighter uppercase italic">{diagnostic?.statut || "Inconnu"}</h2>
              <p className="text-slate-500 text-xs mt-1">{diagnostic?.message || "En attente d'analyse du cœur algorithmique."}</p>
            </div>
          </div>
          <Activity size={100} className="absolute -right-4 -bottom-4 text-slate-800/20" />
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col justify-center text-center">
          <span className="text-[10px] text-slate-500 font-black uppercase mb-2">Fleet_Integrity</span>
          <span className="text-5xl font-black text-white italic">{santeGlobale}{santeGlobale !== "--" ? "%" : ""}</span>
          <div className="w-full bg-slate-800 h-1.5 mt-4 rounded-full overflow-hidden">
            <div className="bg-green-500 h-full transition-all duration-1000" style={{ width: `${santeGlobale === "--" ? 0 : santeGlobale}%` }}></div>
          </div>
        </div>
      </div>

      {/* MATRICE D'INTERVENTION TACTIQUE */}
      {sitesEnAlerte.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-rose-500 text-[10px] font-black uppercase tracking-widest">
            <ShieldAlert size={16} /> Interventions_Requises
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {sitesEnAlerte.map((site, idx) => (
              <ActionCard key={site.espace_id || idx} site={site} onAction={executerActionRapide} disabled={isProcessing} />
            ))}
          </div>
        </section>
      )}

      {/* --- SÉPARATION 50/50 : TÉLÉMÉTRIE VS KPIs GLOBAUX --- */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 items-start pt-4">
        
        {/* COLONNE GAUCHE : LISTE DE TÉLÉMÉTRIE (50%) */}
        <div className="space-y-6">
          <h2 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2 border-b border-slate-800 pb-2">
            <Activity size={16} className="text-green-500" /> Télémétrie par Nœud
          </h2>
          
          <div className="space-y-6">
            {espaces.map((capteur, index) => (
              <div key={capteur.espace_id || index} className="bg-slate-900/30 p-6 rounded-2xl border border-slate-800/50">
                <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-4">Telemetry_Node_{capteur.espace_id || index}</h3>
                
                <div className="flex flex-col gap-3">
                  <MetricCard icon={<Thermometer className="text-orange-400" />} label="Temp_Core" value={capteur.temperature_c} unit="°C" />
                  <MetricCard icon={<Wind className="text-blue-400" />} label="O2_Level" value={capteur.o2_percent} unit="%" />
                  <MetricCard icon={<Droplets className="text-teal-400" />} label="Soil_Sat" value={capteur.humidite_percent} unit="%" />
                  <MetricCard icon={<Activity className="text-purple-400" />} label="CO2_Level" value={capteur.co2_ppm} unit="ppm" />
                </div>

                <div className="flex flex-col items-center mt-6 border-t border-slate-800/50 pt-6">
                  <button 
                    onClick={() => setAfficherPlus(!afficherPlus)}
                    className="group flex items-center gap-2 px-6 py-2 bg-slate-900 hover:bg-slate-800 text-[10px] font-black uppercase tracking-[0.2em] rounded-full border border-slate-700 transition-all shadow-xl"
                  >
                    {afficherPlus ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    {afficherPlus ? "Close_Buffer" : "Open_Extended_Data"}
                  </button>

                  {afficherPlus && (
                    <div className="flex flex-col gap-3 w-full mt-6 animate-in slide-in-from-top-4 duration-300">
                      <MetricCard icon={<Sun className="text-yellow-400" />} label="Lux_Index" value={capteur.luminosite_lux} unit="lx" isSmall />
                      <MetricCard icon={<Droplets className="text-indigo-400" />} label="Res_Eau" value={capteur.reserve_eau_mm} unit="mm" isSmall />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* COLONNE DROITE : TOUR DE CONTRÔLE / KPIs (50%) */}
        <div className="space-y-6 sticky top-6">
          <h2 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-2 border-b border-slate-800 pb-2">
             <Target size={16} className="text-blue-500" /> Analyse de la Flotte
          </h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            
            <GlobalKpiCard 
              title="Global_Soil_Sat" 
              value={saturationGlobale} 
              unit="%" 
              icon={<Droplets size={24} className="text-teal-400" />} 
              status={saturationGlobale !== "--" && saturationGlobale < 40 ? "warning" : "ok"}
            />
            
            <GlobalKpiCard 
              title="Global_CO2_Avg" 
              value={co2Moyen} 
              unit="ppm" 
              icon={<Wind size={24} className="text-purple-400" />} 
              status="ok"
            />

            <GlobalKpiCard 
              title="Thermal_Stress" 
              value={noeudsEnStressThermique} 
              unit="Node(s)" 
              icon={<Thermometer size={24} className={noeudsEnStressThermique > 0 ? "text-red-500" : "text-slate-400"} />} 
              status={noeudsEnStressThermique > 0 ? "critical" : "ok"}
            />

            <GlobalKpiCard 
              title="Vulnerability" 
              value={espaces.length > 0 ? Math.round((sitesEnAlerte.length / espaces.length) * 100) : 0} 
              unit="%" 
              icon={<ShieldAlert size={24} className="text-rose-400" />} 
              status={sitesEnAlerte.length > 0 ? "warning" : "ok"}
            />

          </div>

          {/* Espace réservé pour de futurs contrôles ou graphiques */}
          <div className="bg-slate-900/30 border border-dashed border-slate-700/50 rounded-2xl p-8 flex flex-col items-center justify-center text-center mt-8">
            <Activity size={32} className="text-slate-700 mb-3" />
            <p className="text-slate-500 text-xs uppercase tracking-widest font-black">System_Ready</p>
            <p className="text-slate-600 text-[10px] mt-2 max-w-xs">Espace disponible pour de futurs modules de prédiction IA ou contrôles d'irrigation globale.</p>
          </div>

        </div>

      </div>
    </div>
  );
}

function ActionCard({ site, onAction, disabled }) {
  return (
    <div className="bg-slate-900/80 border-l-4 border-l-rose-500 border border-slate-800 p-4 rounded-lg">
      <div className="flex justify-between items-center mb-3">
        <span className="text-[10px] font-black text-white truncate w-2/3">{site.nom || `Node_${site.espace_id}`}</span>
        <span className="text-[9px] font-bold text-rose-500">{site.sante_percent ?? "--"}% HP</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button onClick={() => onAction(site.espace_id, 'water')} disabled={disabled} className="bg-blue-600 hover:bg-blue-500 text-[9px] font-black py-2 rounded uppercase text-white transition-all">Water</button>
        <button onClick={() => onAction(site.espace_id, 'heat')} disabled={disabled} className="bg-orange-600 hover:bg-orange-500 text-[9px] font-black py-2 rounded uppercase text-white transition-all">Heat</button>
        <button onClick={() => onAction(site.espace_id, 'cover')} disabled={disabled} className="bg-slate-700 hover:bg-slate-600 text-[9px] font-black py-2 rounded uppercase text-white transition-all">Cover</button>
        <button onClick={() => onAction(site.espace_id, 'repair')} disabled={disabled} className="bg-slate-800 hover:bg-slate-700 text-[9px] font-black py-2 rounded uppercase text-slate-400 transition-all flex items-center justify-center gap-1"><Wrench size={10}/> Expert</button>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, unit, isSmall = false }) {
  const displayValue = (value !== null && value !== undefined && value !== "") ? value : "--";
  
  return (
    <div className={`bg-slate-950/50 p-4 rounded-xl border border-slate-800 flex items-center gap-4 group hover:border-slate-500 transition-all ${isSmall ? 'opacity-70' : ''}`}>
      <div className="p-3 bg-slate-900 rounded-lg group-hover:scale-110 transition-transform">{icon}</div>
      <div>
        <p className="text-[8px] text-slate-500 font-black uppercase tracking-widest">{label}</p>
        <div className="flex items-baseline gap-1">
          <p className="text-xl font-black text-white italic">{displayValue}</p>
          <span className="text-[10px] text-slate-600 font-bold">{displayValue !== "--" ? unit : ""}</span>
        </div>
      </div>
    </div>
  );
}

function GlobalKpiCard({ title, value, unit, icon, status }) {
  const statusColors = {
    ok: "border-slate-800",
    warning: "border-amber-500/50 bg-amber-500/5",
    critical: "border-red-500/50 bg-red-500/5"
  };

  return (
    <div className={`p-6 rounded-2xl border transition-colors ${statusColors[status] || statusColors.ok} bg-slate-900`}>
      <div className="flex justify-between items-start mb-4">
        <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
          {icon}
        </div>
      </div>
      <div>
        <div className="flex items-baseline gap-1">
          <span className="text-3xl font-black text-white italic">{value}</span>
          <span className="text-xs text-slate-500 font-bold">{value !== "--" ? unit : ""}</span>
        </div>
        <p className="text-[9px] text-slate-400 font-black uppercase tracking-widest mt-1">{title}</p>
      </div>
    </div>
  );
}