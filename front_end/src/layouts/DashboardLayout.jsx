//DashboardLayout.jsx
import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Outlet, useLocation, Link } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { 
  Sun, 
  CloudRain, 
  Bell, 
  ChevronRight, 
  MapPin, 
  User, 
  MessageSquare, 
  Sprout,
  LogOut
} from "lucide-react";
import { cn } from "../lib/utils";
import Breadcrumbs from "../components/navigation/Breadcrumbs";

export default function DashboardLayout() {
  const [showNotifs, setShowNotifs] = useState(false);
  const [showWeather, setShowWeather] = useState(false);
  const { user, logout, loading } = useAuth(); // Utiliser le hook

  if (loading) return <div className="h-screen w-screen bg-slate-950 flex items-center justify-center text-green-500">Chargement...</div>;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans selection:bg-green-500/30">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0 lg:ml-64 transition-all duration-300">
        <header className="h-16 sticky top-0 z-30 bg-slate-950/80 backdrop-blur-md border-b border-slate-800 px-4 sm:px-8 flex items-center justify-between">
          
          {/* FIL D'ARIANE DYNAMIQUE */}
          <nav className="hidden md:flex items-center text-sm text-slate-400">
            <Breadcrumbs />
          </nav>

          <div className="flex-1 md:hidden"></div>

          <div className="flex items-center gap-4">
            {/* RECTANGLE METEO */}
            <div className="relative">
              <button 
                onClick={() => { setShowWeather(!showWeather); setShowNotifs(false); }}
                className={cn(
                  "flex items-center gap-3 bg-slate-900 border border-slate-800 px-4 py-1.5 rounded-full text-xs shadow-sm transition-all",
                  showWeather ? "border-green-500 ring-1 ring-green-500/20" : "hover:border-slate-600"
                )}
              >
                <Sun className="w-4 h-4 text-amber-400" />
                <span className="font-medium text-slate-300">Lyon: 24°C</span>
              </button>

              {showWeather && (
                <div className="absolute top-12 right-0 w-64 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-4 animate-in zoom-in-95 duration-200">
                  <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">Météo par zone</h4>
                  <div className="space-y-3">
                    {[
                      { zone: "Paris-Nord", temp: "22°C", icon: CloudRain, color: "text-blue-400" },
                      { zone: "Lyon-Est", temp: "24°C", icon: Sun, color: "text-amber-400" },
                      { zone: "Sud-Ouest", temp: "26°C", icon: Sun, color: "text-amber-500" }
                    ].map((m, i) => (
                      <div key={i} className="flex justify-between items-center p-2 hover:bg-slate-800 rounded-lg transition-colors">
                        <span className="text-sm text-slate-300">{m.zone}</span>
                        <div className="flex items-center gap-2">
                          <m.icon size={14} className={m.color} />
                          <span className="text-sm font-bold">{m.temp}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* NOTIFICATIONS CLIQUABLES */}
            <div className="relative">
              <button 
                onClick={() => { setShowNotifs(!showNotifs); setShowWeather(false); }}
                className={cn(
                  "relative p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-full transition-all",
                  showNotifs ? "text-white bg-slate-800" : ""
                )}
              >
                <Bell className="w-5 h-5" />
                <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-slate-950"></span>
              </button>

              {showNotifs && (
                <div className="absolute top-12 right-0 w-80 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                  <div className="p-4 border-b border-slate-800 bg-slate-900/50">
                    <h4 className="text-sm font-bold text-white">Centre de Notifications</h4>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    <NotifItem icon={Sprout} color="text-green-400" title="Santé Végétale" desc="Le Sedum Acre (Zone Nord) a soif." time="Il y a 5 min" />
                    <NotifItem icon={MessageSquare} color="text-blue-400" title="Nouveau Message" desc="Le technicien a terminé l'élagage." time="Il y a 1h" />
                    <NotifItem icon={User} color="text-amber-400" title="Compte" desc="Votre rapport mensuel est prêt." time="Il y a 3h" />
                  </div>
                </div>
              )}
            </div>
            
            <div className="h-8 w-px bg-slate-700 mx-1 hidden sm:block" />

            {/* LE PROFIL A ÉTÉ DÉPLACÉ DANS LA SIDEBAR */}
          </div>
        </header>

        <div className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function NotifItem({ icon: Icon, color, title, desc, time }) {
  return (
    <div className="p-4 border-b border-slate-800/50 hover:bg-slate-800/50 cursor-pointer transition-colors">
      <div className="flex gap-3">
        <div className={cn("p-2 rounded-lg bg-slate-800 shadow-inner", color)}>
          <Icon size={16} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-slate-200">{title}</p>
          <p className="text-xs text-slate-400 truncate">{desc}</p>
          <p className="text-[10px] text-slate-600 mt-1 uppercase font-bold">{time}</p>
        </div>
      </div>
    </div>
  );
}