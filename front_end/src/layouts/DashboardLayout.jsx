import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Bell, Cloud, Sun } from "lucide-react";
import { cn } from "../lib/utils";
import Breadcrumbs from "../components/navigation/Breadcrumbs";
import { api } from "../services/api";

const VILLE_PAR_DEFAUT = "Lyon";

/** Position du navigateur si l'utilisateur l'autorise, sinon null. */
const positionNavigateur = () =>
  new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null);
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lon: p.coords.longitude }),
      () => resolve(null),
      { timeout: 5000, maximumAge: 30 * 60 * 1000 }
    );
  });

export default function DashboardLayout() {
  const [showNotifs, setShowNotifs] = useState(false);
  const [showWeather, setShowWeather] = useState(false);
  const [meteo, setMeteo] = useState(null);
  const [meteoLieu, setMeteoLieu] = useState(VILLE_PAR_DEFAUT);
  const [notifications, setNotifications] = useState([]);
  const { loading } = useAuth();

  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      try {
        const position = await positionNavigateur();
        if (position) {
          setMeteo(await api.getMeteoByCoords(position.lat, position.lon, controller.signal));
          setMeteoLieu("Votre position");
        } else {
          setMeteo(await api.getMeteo(VILLE_PAR_DEFAUT, controller.signal));
        }
      } catch {
        setMeteo(null);
      }
    })();
    api.getNotifications(controller.signal).then(setNotifications).catch(() => {});
    return () => controller.abort();
  }, []);

  const nonLues = notifications.filter((n) => !n.is_read).length;

  const marquerLue = async (notification) => {
    if (notification.is_read) return;
    try {
      const maj = await api.markNotificationAsRead(notification.id);
      setNotifications((liste) => liste.map((n) => (n.id === maj.id ? maj : n)));
    } catch {
      /* sans incidence : la notification reste non lue */
    }
  };

  if (loading) return <div role="status" className="h-screen w-screen bg-slate-950 flex items-center justify-center text-green-500">Chargement…</div>;

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
            {/* MÉTÉO (Open-Meteo via le backend) */}
            <div className="relative">
              <button
                type="button"
                aria-expanded={showWeather}
                onClick={() => { setShowWeather(!showWeather); setShowNotifs(false); }}
                className={cn(
                  "flex items-center gap-3 bg-slate-900 border border-slate-800 px-4 py-1.5 rounded-full text-xs shadow-sm transition-all",
                  showWeather ? "border-green-500 ring-1 ring-green-500/20" : "hover:border-slate-600"
                )}
              >
                {meteo?.ensoleillement_fort ? <Sun className="w-4 h-4 text-amber-400" aria-hidden /> : <Cloud className="w-4 h-4 text-slate-300" aria-hidden />}
                <span className="font-medium text-slate-300">
                  {meteo ? `${meteoLieu} : ${Math.round(meteo.temperature_c)} °C` : "Météo indisponible"}
                </span>
              </button>

              {showWeather && (
                <div className="absolute top-12 right-0 w-64 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-4">
                  <h2 className="text-xs font-bold text-slate-400 uppercase mb-3">Météo actuelle</h2>
                  {meteo ? (
                    <dl className="space-y-2 text-sm">
                      <div className="flex justify-between"><dt className="text-slate-400">Lieu</dt><dd className="text-slate-200">{meteoLieu}</dd></div>
                      <div className="flex justify-between"><dt className="text-slate-400">Température</dt><dd className="font-bold">{meteo.temperature_c} °C</dd></div>
                      <div className="flex justify-between"><dt className="text-slate-400">Ciel</dt><dd>{meteo.condition}</dd></div>
                    </dl>
                  ) : (
                    <p className="text-sm text-slate-400">Le service météo ne répond pas pour le moment.</p>
                  )}
                </div>
              )}
            </div>

            {/* NOTIFICATIONS */}
            <div className="relative">
              <button
                type="button"
                aria-label={nonLues > 0 ? `Notifications (${nonLues} non lues)` : "Notifications"}
                aria-expanded={showNotifs}
                onClick={() => { setShowNotifs(!showNotifs); setShowWeather(false); }}
                className={cn(
                  "relative p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-full transition-all",
                  showNotifs ? "text-white bg-slate-800" : ""
                )}
              >
                <Bell className="w-5 h-5" aria-hidden />
                {nonLues > 0 && <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-slate-950" />}
              </button>

              {showNotifs && (
                <div className="absolute top-12 right-0 w-80 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
                  <div className="p-4 border-b border-slate-800 bg-slate-900/50">
                    <h2 className="text-sm font-bold text-white">Notifications</h2>
                  </div>
                  <ul className="max-h-96 overflow-y-auto">
                    {notifications.length === 0 && (
                      <li className="p-4 text-sm text-slate-400">Aucune notification.</li>
                    )}
                    {notifications.map((n) => (
                      <li key={n.id}>
                        <button
                          type="button"
                          onClick={() => marquerLue(n)}
                          className="w-full text-left p-4 border-b border-slate-800/50 hover:bg-slate-800/50 transition-colors"
                        >
                          <p className={cn("text-sm", n.is_read ? "text-slate-400" : "font-bold text-slate-200")}>{n.message}</p>
                          <p className="text-xs text-slate-500 mt-1">{new Date(n.created_at).toLocaleString("fr-FR")}</p>
                        </button>
                      </li>
                    ))}
                  </ul>
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
