import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Bell, Cloud, Moon, Sun } from "lucide-react";
import { cn } from "../lib/utils";
import Breadcrumbs from "../components/navigation/Breadcrumbs";
import { api } from "../services/api";
import { enregistrerTheme, EVENEMENT_THEME } from "../lib/theme";

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
  const [sombre, setSombre] = useState(() => document.documentElement.dataset.theme === "dark");
  const basculerTheme = () => enregistrerTheme(sombre ? "clair" : "sombre");
  // Reste synchronisé avec la page Paramètres et la préférence système
  useEffect(() => {
    const surTheme = (e) => setSombre(e.detail === "dark");
    window.addEventListener(EVENEMENT_THEME, surTheme);
    return () => window.removeEventListener(EVENEMENT_THEME, surTheme);
  }, []);

  // Échap ferme les panneaux déroulants (météo, notifications)
  useEffect(() => {
    if (!showNotifs && !showWeather) return undefined;
    const surTouche = (e) => {
      if (e.key === "Escape") {
        setShowNotifs(false);
        setShowWeather(false);
      }
    };
    document.addEventListener("keydown", surTouche);
    return () => document.removeEventListener("keydown", surTouche);
  }, [showNotifs, showWeather]);

  const marquerLue = async (notification) => {
    if (notification.is_read) return;
    try {
      const maj = await api.markNotificationAsRead(notification.id);
      setNotifications((liste) => liste.map((n) => (n.id === maj.id ? maj : n)));
    } catch {
      /* sans incidence : la notification reste non lue */
    }
  };

  if (loading) return <div role="status" className="h-screen w-screen bg-canvas flex items-center justify-center text-success">Chargement…</div>;

  return (
    <div className="min-h-screen bg-canvas text-fg flex font-sans">
      <a href="#contenu" className="lien-evitement">Aller au contenu</a>
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0 lg:ml-64">
        <header className="header h-16 sticky top-0 z-30 bg-canvas/90 backdrop-blur-md border-b border-line pl-16 pr-4 sm:pr-8 lg:pl-8 flex items-center justify-between">
          <div className="hidden md:flex items-center text-sm text-fg-muted">
            <Breadcrumbs />
          </div>
          <div className="flex-1 md:hidden" />

          <div className="flex items-center gap-2 sm:gap-4">
            <button
              type="button"
              onClick={basculerTheme}
              aria-label={sombre ? "Passer en thème clair" : "Passer en thème sombre"}
              title={sombre ? "Thème clair" : "Thème sombre"}
              className="rounded-full p-2 text-fg-muted hover:bg-surface-raised hover:text-fg"
            >
              {sombre ? <Sun className="h-5 w-5" aria-hidden /> : <Moon className="h-5 w-5" aria-hidden />}
            </button>

            {/* MÉTÉO (Open-Meteo via le backend) */}
            <div className="relative">
              <button
                type="button"
                aria-expanded={showWeather}
                onClick={() => { setShowWeather(!showWeather); setShowNotifs(false); }}
                className={cn(
                  "flex items-center gap-3 bg-surface border border-line px-4 py-1.5 rounded-full text-xs shadow-sm transition-all",
                  showWeather ? "border-success ring-1 ring-focus/20" : "hover:border-line-strong"
                )}
              >
                {meteo?.ensoleillement_fort ? <Sun className="w-4 h-4 text-warning" aria-hidden /> : <Cloud className="w-4 h-4 text-fg-soft" aria-hidden />}
                <span className="hidden font-medium text-fg-soft sm:inline">
                  {meteo ? `${meteoLieu} : ${Math.round(meteo.temperature_c)} °C` : "Météo indisponible"}
                </span>
              </button>

              {showWeather && (
                <div className="absolute top-12 right-0 w-64 bg-surface border border-line rounded-2xl shadow-2xl p-4">
                  <h2 className="text-xs font-bold text-fg-muted uppercase mb-3">Météo actuelle</h2>
                  {meteo ? (
                    <dl className="space-y-2 text-sm">
                      <div className="flex justify-between"><dt className="text-fg-muted">Lieu</dt><dd className="text-fg">{meteoLieu}</dd></div>
                      <div className="flex justify-between"><dt className="text-fg-muted">Température</dt><dd className="font-bold">{meteo.temperature_c} °C</dd></div>
                      <div className="flex justify-between"><dt className="text-fg-muted">Ciel</dt><dd>{meteo.condition}</dd></div>
                    </dl>
                  ) : (
                    <p className="text-sm text-fg-muted">Le service météo ne répond pas pour le moment.</p>
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
                  "relative p-2 text-fg-muted hover:text-fg hover:bg-surface-raised rounded-full transition-all",
                  showNotifs ? "text-fg bg-surface-raised" : ""
                )}
              >
                <Bell className="w-5 h-5" aria-hidden />
                {nonLues > 0 && <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-canvas" />}
              </button>

              {showNotifs && (
                <div className="absolute top-12 right-0 w-80 bg-surface border border-line rounded-2xl shadow-2xl overflow-hidden">
                  <div className="p-4 border-b border-line bg-surface/50">
                    <h2 className="text-sm font-bold text-fg">Notifications</h2>
                  </div>
                  <ul className="max-h-96 overflow-y-auto">
                    {notifications.length === 0 && (
                      <li className="p-4 text-sm text-fg-muted">Aucune notification.</li>
                    )}
                    {notifications.map((n) => (
                      <li key={n.id}>
                        <button
                          type="button"
                          onClick={() => marquerLue(n)}
                          className="w-full text-left p-4 border-b border-line/50 hover:bg-surface-raised/50 transition-colors"
                        >
                          <p className={cn("text-sm", n.is_read ? "text-fg-muted" : "font-bold text-fg")}>{n.message}</p>
                          <p className="text-xs text-fg-muted mt-1">{new Date(n.created_at).toLocaleString("fr-FR")}</p>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            
          </div>
        </header>

        <main id="contenu" tabIndex={-1} className="main-content flex-1 p-4 sm:p-6 lg:p-8 focus:outline-none">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
