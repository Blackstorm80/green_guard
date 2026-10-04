import { useCallback, useMemo, useState } from "react";
import { CheckCircle2, Download, Printer } from "lucide-react";
import { api } from "../../services/api";
import { useAuth } from "../../context/AuthContext";
import { useRequete, useTitrePage } from "../../lib/hooks";
import { LIBELLES_INTERVENTION, LIBELLES_STATUT_INTERVENTION, peut } from "../../lib/referentiels";
import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { Alert, Badge, Card } from "../../components/ui/Card";
import { ModaleArrosage } from "../../components/interventions/ModaleArrosage";

const TON_STATUT = { planifiee: "info", en_cours: "alerte", terminee: "succes" };
const FILTRES_INITIAUX = { du: "", au: "", espaceId: "", type: "", statut: "", recherche: "" };

const chargerDonnees = async (signal) => {
  const [interventions, espaces] = await Promise.all([api.getInterventions(undefined, signal), api.getEspacesVerts(signal)]);
  return { interventions, espaces };
};

const formatVolume = (litres) => (typeof litres === "number" ? `${litres.toLocaleString("fr-FR")} L` : "—");
const formatDate = (iso) => (iso ? new Date(iso).toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" }) : "—");

/** Export CSV compatible Excel (séparateur « ; », BOM UTF-8, champs échappés). */
function exporterCsv(lignes, nomEspace) {
  const echapper = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const entete = ["Créée le", "Espace", "Type", "Description", "Volume (L)", "Statut", "Réalisée le"];
  const corps = lignes.map((i) => [
    formatDate(i.cree_le), nomEspace(i.espace_id), LIBELLES_INTERVENTION[i.type] ?? i.type, i.description,
    i.volume_eau_l, LIBELLES_STATUT_INTERVENTION[i.statut] ?? i.statut, formatDate(i.realisee_le),
  ]);
  const csv = [entete, ...corps].map((l) => l.map(echapper).join(";")).join("\r\n");
  const lien = document.createElement("a");
  lien.href = URL.createObjectURL(new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" }));
  lien.download = `greenguard-interventions-${new Date().toISOString().slice(0, 10)}.csv`;
  lien.click();
  URL.revokeObjectURL(lien.href);
}

export default function Rapports() {
  useTitrePage("Rapports");
  const { user } = useAuth();
  const peutIntervenir = peut(user, "interventions");
  const { donnees, setDonnees, chargement, erreur } = useRequete(chargerDonnees, { interventions: [], espaces: [] });
  const [filtres, setFiltres] = useState(FILTRES_INITIAUX);
  const [erreurAction, setErreurAction] = useState("");
  const [aTerminer, setATerminer] = useState(null);
  const majFiltre = (champ) => (e) => setFiltres((f) => ({ ...f, [champ]: e.target.value }));

  const nomsEspaces = useMemo(() => Object.fromEntries(donnees.espaces.map((e) => [e.id, e.nom])), [donnees.espaces]);
  const nomEspace = useCallback((id) => nomsEspaces[id] ?? `Espace n°${id}`, [nomsEspaces]);

  const lignes = useMemo(() => {
    const du = filtres.du ? new Date(`${filtres.du}T00:00:00`) : null;
    const au = filtres.au ? new Date(`${filtres.au}T23:59:59`) : null;
    const recherche = filtres.recherche.trim().toLowerCase();
    return donnees.interventions.filter((i) => {
      const date = new Date(i.cree_le);
      if (du && date < du) return false;
      if (au && date > au) return false;
      if (filtres.espaceId && String(i.espace_id) !== filtres.espaceId) return false;
      if (filtres.type && i.type !== filtres.type) return false;
      if (filtres.statut && i.statut !== filtres.statut) return false;
      if (recherche && !`${i.description ?? ""} ${nomEspace(i.espace_id)}`.toLowerCase().includes(recherche)) return false;
      return true;
    });
  }, [donnees.interventions, filtres, nomEspace]);

  const synthese = useMemo(() => ({
    total: lignes.length,
    aFaire: lignes.filter((i) => i.statut !== "terminee").length,
    terminees: lignes.filter((i) => i.statut === "terminee").length,
    volume: lignes.reduce((s, i) => s + (i.volume_eau_l ?? 0), 0),
  }), [lignes]);

  const remplacer = (maj) =>
    setDonnees((d) => ({ ...d, interventions: d.interventions.map((i) => (i.id === maj.id ? maj : i)) }));

  const terminer = async (intervention) => {
    setErreurAction("");
    // Un arrosage se termine avec son volume réel : c'est lui qui est compté dans le bilan
    if (intervention.type === "arrosage") {
      setATerminer(intervention);
      return;
    }
    try {
      remplacer(await api.updateIntervention(intervention.id, { statut: "terminee" }));
    } catch (err) {
      setErreurAction(err.message);
    }
  };

  const terminerArrosage = async ({ volume_eau_l }) => {
    remplacer(await api.updateIntervention(aTerminer.id, { statut: "terminee", volume_eau_l }));
    setATerminer(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-fg">Rapports</h1>
          <p className="mt-1 text-fg-muted">Historique des interventions sur vos espaces verts.</p>
        </div>
        <div className="no-print flex gap-2">
          <Button variante="secondaire" icone={Printer} onClick={() => window.print()}>Imprimer</Button>
          <Button icone={Download} onClick={() => exporterCsv(lignes, nomEspace)} disabled={!lignes.length}>
            Exporter en CSV
          </Button>
        </div>
      </div>

      <Card as="form" aria-label="Filtres" className="no-print grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-6"
            onSubmit={(e) => e.preventDefault()}>
        <Field label="Du" type="date" value={filtres.du} onChange={majFiltre("du")} />
        <Field label="Au" type="date" value={filtres.au} onChange={majFiltre("au")} />
        <Field label="Espace">
          {(a11y) => (
            <select {...a11y} value={filtres.espaceId} onChange={majFiltre("espaceId")}>
              <option value="">Tous</option>
              {donnees.espaces.map((e) => <option key={e.id} value={e.id}>{e.nom}</option>)}
            </select>
          )}
        </Field>
        <Field label="Type">
          {(a11y) => (
            <select {...a11y} value={filtres.type} onChange={majFiltre("type")}>
              <option value="">Tous</option>
              {Object.entries(LIBELLES_INTERVENTION).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          )}
        </Field>
        <Field label="Statut">
          {(a11y) => (
            <select {...a11y} value={filtres.statut} onChange={majFiltre("statut")}>
              <option value="">Tous</option>
              {Object.entries(LIBELLES_STATUT_INTERVENTION).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          )}
        </Field>
        <Field label="Recherche" type="search" placeholder="Description, espace…" value={filtres.recherche}
               onChange={majFiltre("recherche")} />
      </Card>

      <dl className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[
          ["Interventions", synthese.total],
          ["À réaliser", synthese.aFaire],
          ["Terminées", synthese.terminees],
          ["Eau apportée", `${synthese.volume.toLocaleString("fr-FR")} L`],
        ].map(([libelle, valeur]) => (
          <Card key={libelle} as="div" className="p-4 sm:p-5">
            <dt className="text-sm text-fg-muted">{libelle}</dt>
            <dd className="mt-1 text-2xl font-bold text-fg">{valeur}</dd>
          </Card>
        ))}
      </dl>

      {erreur && <Alert ton="danger">{erreur}</Alert>}
      {erreurAction && <Alert ton="danger">{erreurAction}</Alert>}
      {aTerminer && (
        <ModaleArrosage
          titre={`Terminer l'arrosage : ${nomEspace(aTerminer.espace_id)}`}
          description="Saisissez le volume réellement apporté."
          volumeInitial={aTerminer.volume_eau_l ?? undefined}
          aide="Compté aussitôt dans le bilan hydrique (volume / surface de l'espace). Vide : rien n'est compté."
          libelleValider="Terminer l'arrosage"
          onValider={terminerArrosage}
          onClose={() => setATerminer(null)}
        />
      )}

      {/* relative : contient les éléments sr-only (position absolue) dans la zone défilante */}
      <Card className="relative overflow-x-auto p-0 sm:p-0">
        <table className="w-full min-w-[800px] text-left text-sm">
          <caption className="sr-only">Interventions filtrées ({lignes.length})</caption>
          <thead className="border-b border-line bg-surface-raised text-fg-muted">
            <tr>
              {["Créée le", "Espace", "Type", "Description", "Volume", "Statut", ""].map((titre, i) => (
                <th key={titre || i} scope="col" className="px-4 py-3 font-semibold">
                  {titre || <span className="sr-only">Actions</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {chargement && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-fg-muted" role="status">Chargement…</td></tr>
            )}
            {!chargement && lignes.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-fg-muted">
                  {donnees.interventions.length
                    ? "Aucune intervention ne correspond à ces filtres."
                    : "Aucune intervention pour le moment. Elles se créent depuis le tableau de bord, sur les espaces en alerte."}
                </td>
              </tr>
            )}
            {lignes.map((i) => (
              <tr key={i.id} className="text-fg-soft">
                <td className="whitespace-nowrap px-4 py-3">{formatDate(i.cree_le)}</td>
                <td className="px-4 py-3 font-medium text-fg">{nomEspace(i.espace_id)}</td>
                <td className="px-4 py-3">{LIBELLES_INTERVENTION[i.type] ?? i.type}</td>
                <td className="px-4 py-3">{i.description || "—"}</td>
                <td className="whitespace-nowrap px-4 py-3">
                  {formatVolume(i.volume_eau_l)}
                  {i.arrosage_compte_mm !== null && i.arrosage_compte_mm !== undefined && (
                    <span className="block text-xs text-fg-muted">
                      {i.arrosage_compte_mm.toLocaleString("fr-FR", { maximumFractionDigits: 1 })} mm comptés
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <Badge ton={TON_STATUT[i.statut]}>{LIBELLES_STATUT_INTERVENTION[i.statut] ?? i.statut}</Badge>
                </td>
                <td className="px-4 py-3 text-right">
                  {i.statut !== "terminee" && peutIntervenir && (
                    <Button variante="fantome" taille="sm" icone={CheckCircle2} onClick={() => terminer(i)}
                            className="no-print" aria-label={`Marquer terminée : ${LIBELLES_INTERVENTION[i.type] ?? i.type}, ${nomEspace(i.espace_id)}`}>
                      Terminer
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
