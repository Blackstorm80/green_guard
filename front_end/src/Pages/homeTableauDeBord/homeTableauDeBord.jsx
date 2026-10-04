import { useCallback, useEffect, useState } from "react";
import {
  Activity, AlertTriangle, CheckCircle, ChevronDown, ChevronUp, Clock, Cpu, Droplets,
  CalendarClock, ShieldAlert, Stethoscope, Sun, Target, Thermometer, Umbrella, Wind,
} from "lucide-react";
import { api } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import { useRequete, useTitrePage } from "../../lib/hooks";
import { DECISIONS_PREVISION, peut, TON_STATUT } from "../../lib/referentiels";
import { Badge } from "../../components/ui/Card";
import { ModaleArrosage } from "../../components/interventions/ModaleArrosage";

const INTERVALLE_RAFRAICHISSEMENT_MS = 30000;
const STATUTS_EN_ALERTE = ["Critique", "A surveiller"];
const ACTIONS = [
  { type: "arrosage", label: "Arroser", icon: Droplets, classe: "bg-blue-600 hover:bg-blue-700 text-on-accent" },
  { type: "ombrage", label: "Ombrager", icon: Umbrella, classe: "bg-orange-700 hover:bg-orange-800 text-on-accent" },
  { type: "diagnostic", label: "Diagnostic", icon: Stethoscope, classe: "bg-surface-strong hover:bg-line-strong text-fg" },
];

const formatNombre = (v, decimales = 0) =>
  typeof v === "number" ? v.toLocaleString("fr-FR", { maximumFractionDigits: decimales }) : "--";

/** Aide du champ volume : dose recommandée (mm, litres, minutes) calculée par le bilan. */
function aideDose(dose) {
  if (!dose) return "Aucune dose calculée pour cet espace (bilan hydrique pas encore disponible).";
  if (dose.litres === null) {
    return `Dose recommandée : ${formatNombre(dose.mm, 1)} mm. Renseignez la surface de l'espace pour l'obtenir en litres.`;
  }
  const minutes = dose.minutes !== null ? `, soit ${formatNombre(dose.minutes)} min au débit de l'arrosage` : "";
  return `Dose recommandée pour remplir la réserve : ${formatNombre(dose.mm, 1)} mm, ${formatNombre(dose.litres)} L${minutes}. Modifiable.`;
}

export default function HomeTableauDeBord() {
  useTitrePage("Tableau de bord");
  const { user } = useAuth();
  const peutIntervenir = peut(user, "interventions");
  const [dashboard, setDashboard] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [ouverts, setOuverts] = useState({});
  const [actionEnCours, setActionEnCours] = useState(null);
  const [arrosage, setArrosage] = useState(null);

  const charger = useCallback(async (signal) => {
    try {
      const data = await api.getDashboardStats([], signal);
      setDashboard(data);
      setLastUpdate(new Date().toLocaleTimeString("fr-FR"));
      setError(null);
    } catch (err) {
      if (err.name === "AbortError") return;
      setError("Impossible de récupérer les données du tableau de bord.");
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    charger(controller.signal);
    // Pas de rafraîchissement quand l'onglet est masqué
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") charger(controller.signal);
    }, INTERVALLE_RAFRAICHISSEMENT_MS);
    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, [charger]);

  const declencherIntervention = async (site, action) => {
    if (action.type === "arrosage") {
      setFeedback(null);
      setArrosage(site);
      return;
    }
    setActionEnCours(`${site.espace_id}-${action.type}`);
    setFeedback(null);
    try {
      await api.createIntervention({
        espace_id: site.espace_id,
        type: action.type,
        description: `Déclenchée depuis le tableau de bord (statut : ${site.statut})`,
      });
      setFeedback({ ok: true, message: `Intervention « ${action.label} » planifiée pour ${site.nom}.` });
    } catch (err) {
      setFeedback({ ok: false, message: err.message });
    } finally {
      setActionEnCours(null);
    }
  };

  const creerArrosage = async ({ volume_eau_l, terminee }) => {
    const site = arrosage;
    const creee = await api.createIntervention({
      espace_id: site.espace_id,
      type: "arrosage",
      description: `Déclenchée depuis le tableau de bord (statut : ${site.statut})`,
      volume_eau_l,
      statut: terminee ? "terminee" : "planifiee",
    });
    setArrosage(null);
    if (creee.arrosage_compte_mm !== null) {
      setFeedback({ ok: true, message: `Arrosage de ${site.nom} enregistré : ${formatNombre(creee.arrosage_compte_mm, 1)} mm comptés dans le bilan.` });
      charger();
    } else {
      setFeedback({ ok: true, message: terminee
        ? `Arrosage de ${site.nom} enregistré sans volume : rien n'est compté dans le bilan.`
        : `Arrosage planifié pour ${site.nom}.` });
    }
  };

  if (loading && !dashboard) {
    return (
      <div role="status" className="flex flex-col items-center justify-center h-64 space-y-4">
        <div className="w-10 h-10 border-2 border-success/20 border-t-green-500 rounded-full animate-spin" />
        <p className="text-sm text-success">Chargement du tableau de bord…</p>
      </div>
    );
  }

  const capteurs = dashboard?.capteurs ?? [];
  const metrics = dashboard?.metrics;
  const sitesEnAlerte = capteurs.filter((c) => STATUTS_EN_ALERTE.includes(c.statut));
  const isSain = dashboard?.statut === "Sain";
  const sante = metrics?.sante_globale_percent;
  const humiditeMoyenne = (() => {
    const valeurs = capteurs.map((c) => c.humidite_percent).filter((v) => typeof v === "number");
    return valeurs.length ? valeurs.reduce((a, b) => a + b, 0) / valeurs.length : null;
  })();
  const stressThermique = capteurs.filter(
    (c) => typeof c.temperature_c === "number" && (c.temperature_c < 15 || c.temperature_c > 30)
  ).length;
  const vulnerabilite = metrics?.espaces_avec_donnees
    ? (metrics.espaces_stress / metrics.espaces_avec_donnees) * 100
    : null;

  return (
    <div className="space-y-6 text-fg-soft">
      <h1 className="text-3xl font-bold tracking-tight text-fg">Tableau de bord</h1>

      {/* BARRE DE STATUT */}
      <div className="flex flex-wrap gap-3 justify-between items-center bg-surface/50 border border-line p-3 rounded-lg text-xs font-bold uppercase tracking-wide">
        <div className="flex gap-6">
          <span className="flex items-center gap-2"><Cpu size={14} className="text-success" /> Espaces suivis : {metrics?.espaces_suivis ?? 0}</span>
          {dashboard?.meteo_exterieure && (
            <span className="flex items-center gap-2 text-info">
              <Sun size={14} /> Extérieur : {formatNombre(dashboard.meteo_exterieure.temperature_c, 1)} °C, {dashboard.meteo_exterieure.condition}
            </span>
          )}
        </div>
        <span className="flex items-center gap-2 text-fg bg-surface-raised px-3 py-1 rounded border border-line-strong">
          <Clock size={12} /> {lastUpdate || "--:--:--"}
        </span>
      </div>

      {error && (
        <div role="alert" className="bg-danger-soft border border-danger-line text-danger p-3 rounded-lg text-sm font-bold flex items-center gap-2">
          <AlertTriangle size={16} /> {error}
        </div>
      )}
      {feedback && (
        <div role="status" className={`p-3 rounded-lg text-sm font-bold border ${feedback.ok ? "bg-success-soft border-success/20 text-success" : "bg-danger-soft border-danger-line text-danger"}`}>
          {feedback.message}
        </div>
      )}

      {/* SYNTHÈSE */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 p-6 rounded-2xl border-2 bg-surface border-line relative overflow-hidden">
          <div className="flex items-center gap-6 relative z-10">
            <div className={`p-4 rounded-xl ${isSain ? "bg-primary text-on-accent" : "bg-amber-500 text-slate-950"}`}>
              {isSain ? <CheckCircle size={32} aria-hidden /> : <AlertTriangle size={32} aria-hidden />}
            </div>
            <div>
              <h2 className="text-3xl font-black text-fg tracking-tight">{dashboard?.statut ?? "Inconnu"}</h2>
              <p className="text-fg-muted text-sm mt-1">{dashboard?.message}</p>
            </div>
          </div>
          <Activity size={100} className="absolute -right-4 -bottom-4 text-fg-subtle/20" aria-hidden />
        </div>

        <div className="bg-surface border border-line p-6 rounded-2xl flex flex-col justify-center text-center">
          <span className="text-xs text-fg-muted font-bold uppercase mb-2">Santé globale</span>
          <span className="text-5xl font-black text-fg">{formatNombre(sante)}{typeof sante === "number" ? " %" : ""}</span>
          <div className="w-full bg-surface-raised h-1.5 mt-4 rounded-full overflow-hidden" role="progressbar"
               aria-valuenow={sante ?? 0} aria-valuemin={0} aria-valuemax={100} aria-label="Santé globale">
            <div className="bg-primary h-full transition-all duration-1000" style={{ width: `${sante ?? 0}%` }} />
          </div>
        </div>
      </div>

      {/* INTERVENTIONS REQUISES */}
      {sitesEnAlerte.length > 0 && (
        <section className="space-y-4" aria-labelledby="titre-interventions">
          <h2 id="titre-interventions" className="flex items-center gap-2 text-danger text-sm font-black uppercase tracking-wide">
            <ShieldAlert size={16} aria-hidden /> Interventions requises
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {sitesEnAlerte.map((site) => (
              <ActionCard key={site.espace_id} site={site} actionEnCours={actionEnCours}
                          onAction={peutIntervenir ? declencherIntervention : null} />
            ))}
          </div>
        </section>
      )}

      {arrosage && (
        <ModaleArrosage
          titre={`Arroser « ${arrosage.nom} »`}
          description="Volume pré-rempli avec la dose recommandée par le bilan hydrique."
          volumeInitial={arrosage.dose_recommandee?.litres ?? undefined}
          aide={aideDose(arrosage.dose_recommandee)}
          libelleValider="Enregistrer l'arrosage"
          proposerTerminee
          onValider={creerArrosage}
          onClose={() => setArrosage(null)}
        />
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 items-start pt-4">
        {/* TÉLÉMÉTRIE PAR ESPACE */}
        <section className="space-y-6" aria-labelledby="titre-telemetrie">
          <h2 id="titre-telemetrie" className="text-sm font-black text-fg uppercase tracking-wide flex items-center gap-2 border-b border-line pb-2">
            <Activity size={16} className="text-success" aria-hidden /> Télémétrie par espace
          </h2>
          {capteurs.length === 0 && (
            <p className="text-fg-muted text-sm">Ajoutez un espace vert pour commencer le suivi.</p>
          )}
          {capteurs.map((capteur) => {
            const ouvert = Boolean(ouverts[capteur.espace_id]);
            return (
              <article key={capteur.espace_id} className="bg-surface/30 p-6 rounded-2xl border border-line/50">
                <header className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-black text-fg">{capteur.nom}</h3>
                  <Badge ton={TON_STATUT[capteur.statut] ?? "neutre"}>{capteur.statut}</Badge>
                </header>
                <DecisionPrevision decision={capteur.decision} dateBascule={capteur.date_bascule} dateCalcul={dashboard?.date_calcul} />
                <div className="flex flex-col gap-3">
                  <MetricCard icon={<Thermometer className="text-orange-400" />} label="Température" value={formatNombre(capteur.temperature_c, 1)} unit="°C" />
                  <MetricCard icon={<Droplets className="text-teal-400" />} label="Humidité du sol" value={formatNombre(capteur.humidite_percent, 1)} unit="%" />
                  <MetricCard icon={<Wind className="text-info" />} label="Humidité de l'air" value={formatNombre(capteur.humidite_air_percent)} unit="%" />
                </div>
                <div className="flex flex-col items-center mt-6 border-t border-line/50 pt-6">
                  <button
                    type="button"
                    aria-expanded={ouvert}
                    onClick={() => setOuverts((o) => ({ ...o, [capteur.espace_id]: !ouvert }))}
                    className="flex items-center gap-2 px-6 py-2 bg-surface hover:bg-surface-raised text-xs font-bold uppercase tracking-wide rounded-full border border-line-strong focus:outline-none focus-visible:ring-2 focus-visible:ring-focus"
                  >
                    {ouvert ? <ChevronUp size={14} aria-hidden /> : <ChevronDown size={14} aria-hidden />}
                    {ouvert ? "Masquer le détail" : "Voir le détail"}
                  </button>
                  {ouvert && (
                    <div className="flex flex-col gap-3 w-full mt-6">
                      <MetricCard icon={<Droplets className="text-indigo-400" />} label="Réserve en eau" value={formatNombre(capteur.reserve_eau_mm, 1)}
                                  unit={typeof capteur.reserve_max_mm === "number" ? `mm sur ${formatNombre(capteur.reserve_max_mm, 1)} mm` : "mm"} />
                      <MetricCard icon={<Sun className="text-amber-400" />} label="Consommation du jour" value={formatNombre(capteur.etc_mm, 1)} unit="mm" />
                      {capteur.dose_recommandee?.mm > 0 && (
                        <MetricCard icon={<Droplets className="text-blue-400" />} label="Dose pour remplir la réserve"
                                    value={formatNombre(capteur.dose_recommandee.litres ?? capteur.dose_recommandee.mm, 1)}
                                    unit={capteur.dose_recommandee.litres !== null
                                      ? `L (${formatNombre(capteur.dose_recommandee.mm, 1)} mm${capteur.dose_recommandee.minutes !== null ? `, ${formatNombre(capteur.dose_recommandee.minutes)} min` : ""})`
                                      : "mm"} />
                      )}
                      <ExplicationReserve espaceId={capteur.espace_id} />
                      <MetricCard icon={<Activity className="text-purple-400" />} label="CO₂" value={formatNombre(capteur.co2_ppm)} unit="ppm" />
                    </div>
                  )}
                </div>
              </article>
            );
          })}
        </section>

        {/* ANALYSE DU PARC */}
        <section className="space-y-6 xl:sticky xl:top-6" aria-labelledby="titre-analyse">
          <h2 id="titre-analyse" className="text-sm font-black text-fg uppercase tracking-wide flex items-center gap-2 border-b border-line pb-2">
            <Target size={16} className="text-info" aria-hidden /> Analyse du parc
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <GlobalKpiCard title="Humidité moyenne du sol" value={formatNombre(humiditeMoyenne)} unit="%"
              icon={<Droplets size={24} className="text-teal-400" />}
              status={humiditeMoyenne !== null && humiditeMoyenne < 40 ? "warning" : "ok"} />
            <GlobalKpiCard title={`Qualité de l'air (${metrics?.qualite_air ?? "Inconnue"})`} value={formatNombre(metrics?.co2_moyen_ppm)} unit="ppm"
              icon={<Wind size={24} className="text-purple-400" />} status="ok" />
            <GlobalKpiCard title="Stress thermique" value={stressThermique} unit="espace(s)"
              icon={<Thermometer size={24} className={stressThermique > 0 ? "text-danger" : "text-fg-muted"} />}
              status={stressThermique > 0 ? "critical" : "ok"} />
            <GlobalKpiCard title="Espaces en alerte" value={formatNombre(vulnerabilite)} unit="%"
              icon={<ShieldAlert size={24} className="text-danger" />}
              status={sitesEnAlerte.length > 0 ? "warning" : "ok"} />
          </div>
        </section>
      </div>
    </div>
  );
}

function ActionCard({ site, onAction, actionEnCours }) {
  return (
    <div className="bg-surface/80 border-l-4 border-l-rose-500 border border-line p-4 rounded-lg">
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm font-bold text-fg truncate w-2/3">{site.nom}</span>
        <span className="text-xs font-bold text-danger">{formatNombre(site.sante_percent)} % santé</span>
      </div>
      {/* Rôle lecteur : l'alerte est visible, les actions terrain ne sont pas proposées */}
      {onAction && <div className="grid grid-cols-3 gap-2">
        {ACTIONS.map((action) => {
          const Icone = action.icon;
          const enCours = actionEnCours === `${site.espace_id}-${action.type}`;
          return (
            <button
              key={action.type}
              type="button"
              onClick={() => onAction(site, action)}
              disabled={Boolean(actionEnCours)}
              className={`${action.classe} text-xs font-bold py-2 rounded flex items-center justify-center gap-1 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-white`}
            >
              <Icone size={12} aria-hidden /> {enCours ? "…" : action.label}
            </button>
          );
        })}
      </div>}
    </div>
  );
}

const formatJour = (iso) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long" });

/** Décision de la prévision à 7 jours : badge et phrase calculée ; rien si la météo prévue est indisponible. */
function DecisionPrevision({ decision, dateBascule, dateCalcul }) {
  if (!decision) return null;
  const { libelle, ton } = DECISIONS_PREVISION[decision.code] ?? { libelle: decision.code, ton: "neutre" };
  // Déjà critique aujourd'hui : le badge de statut le dit, la phrase dit quoi faire.
  // Comparaison au jour métier du serveur (dates ISO), pas à l'horloge ni au fuseau du navigateur
  const basculeAVenir = Boolean(dateBascule && dateCalcul && dateBascule > dateCalcul);
  return (
    <div className="mb-4 flex flex-col gap-2 rounded-xl border border-line bg-canvas/50 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge ton={ton}><CalendarClock size={12} aria-hidden /> Prévision : {libelle}</Badge>
        {basculeAVenir && <span className="text-xs text-fg-muted">Critique prévu le {formatJour(dateBascule)}</span>}
      </div>
      <p className="text-sm text-fg-soft">{decision.texte}</p>
    </div>
  );
}

/** Phrase « pourquoi » calculée par le diagnostic (lecture seule), chargée à l'ouverture du détail. */
function ExplicationReserve({ espaceId }) {
  const charger = useCallback(() => api.diagnostiquerEspace(espaceId), [espaceId]);
  const { donnees, chargement } = useRequete(charger);
  if (chargement) return <p role="status" className="text-xs text-fg-muted">Calcul de l'explication…</p>;
  if (!donnees?.explication) return null;
  return <p className="text-sm text-fg-soft bg-canvas/50 p-4 rounded-xl border border-line">{donnees.explication}</p>;
}

function MetricCard({ icon, label, value, unit }) {
  return (
    <div className="bg-canvas/50 p-4 rounded-xl border border-line flex items-center gap-4">
      <div className="p-3 bg-surface rounded-lg" aria-hidden>{icon}</div>
      <div>
        <p className="text-xs text-fg-muted font-bold uppercase tracking-wide">{label}</p>
        <p className="flex items-baseline gap-1">
          <span className="text-xl font-black text-fg">{value}</span>
          <span className="text-xs text-fg-muted font-bold">{value !== "--" ? unit : ""}</span>
        </p>
      </div>
    </div>
  );
}

function GlobalKpiCard({ title, value, unit, icon, status }) {
  const statusColors = {
    ok: "border-line",
    warning: "border-warning/40 bg-warning-soft",
    critical: "border-danger-line bg-danger-soft",
  };
  return (
    <div className={`p-6 rounded-2xl border bg-surface ${statusColors[status] || statusColors.ok}`}>
      <div className="p-2 bg-canvas rounded-lg border border-line w-fit mb-4" aria-hidden>{icon}</div>
      <p className="flex items-baseline gap-1">
        <span className="text-3xl font-black text-fg">{value}</span>
        <span className="text-xs text-fg-muted font-bold">{value !== "--" ? unit : ""}</span>
      </p>
      <p className="text-xs text-fg-muted font-bold uppercase tracking-wide mt-1">{title}</p>
    </div>
  );
}
