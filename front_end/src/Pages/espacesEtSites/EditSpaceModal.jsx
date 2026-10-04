import { useState } from "react";
import { Trash2 } from "lucide-react";
import { api } from "../../services/api";
import { Modal } from "../../components/ui/Modal";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Card";
import { Champ, Choix } from "./champsEspace";
import { DRAINAGES, EXPOSITIONS, IRRIGATIONS, TYPES_SOL } from "../../lib/referentiels";

const CHAMPS_NUMERIQUES = new Set([
  "surface_m2", "ph_actuel", "humidite_cible", "frequence_arrosage_auto", "profondeur_racinaire",
  "reserve_utile_max", "coefficient_cultural", "debit_arrosage_l_min",
]);

const valeursInitiales = (espace) => ({
  nom: espace?.nom ?? "",
  ville: espace?.ville ?? "",
  surface_m2: espace?.surface_m2 ?? "",
  type_sol: espace?.type_sol ?? "",
  ph_actuel: espace?.ph_actuel ?? "",
  exposition: espace?.exposition ?? "",
  drainage: espace?.drainage ?? "",
  humidite_cible: espace?.humidite_cible ?? "",
  frequence_arrosage_auto: espace?.frequence_arrosage_auto ?? "",
  profondeur_racinaire: espace?.profondeur_racinaire ?? "",
  reserve_utile_max: espace?.reserve_utile_max ?? "",
  coefficient_cultural: espace?.coefficient_cultural ?? "",
  type_irrigation: espace?.type_irrigation ?? "",
  debit_arrosage_l_min: espace?.debit_arrosage_l_min ?? "",
  date_derniere_fertilisation: espace?.date_derniere_fertilisation ?? "",
});

const formatMm = (v) => (typeof v === "number" ? v.toLocaleString("fr-FR", { maximumFractionDigits: 1 }) : "--");

export default function EditSpaceModal({ espace, onClose, onSuccess }) {
  // Le parent monte la modale avec l'espace sélectionné : l'état initial suffit
  const [valeurs, setValeurs] = useState(() => valeursInitiales(espace));
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [confirmerSuppression, setConfirmerSuppression] = useState(false);
  const onChange = (e) => setValeurs((v) => ({ ...v, [e.target.name]: e.target.value }));
  const lie = { valeurs, onChange };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErreur("");
    setEnvoi(true);
    // Champs vides omis (inchangés côté serveur), champs numériques convertis
    const payload = Object.fromEntries(
      Object.entries(valeurs)
        .filter(([, v]) => v !== "" && v !== null && v !== undefined)
        .map(([k, v]) => [k, CHAMPS_NUMERIQUES.has(k) ? Number(v) : v])
    );
    // Réserve vidée : retour à la réserve calculée (FAO-56) plutôt que « inchangée »
    if (valeurs.reserve_utile_max === "" && espace.reserve_utile_max != null) payload.reserve_utile_max = null;
    if (valeurs.debit_arrosage_l_min === "" && espace.debit_arrosage_l_min != null) payload.debit_arrosage_l_min = null;
    try {
      await api.updateEspace(espace.id, payload);
      onSuccess();
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  };

  const supprimer = async () => {
    setErreur("");
    setEnvoi(true);
    try {
      await api.deleteEspace(espace.id);
      onSuccess();
    } catch (err) {
      setErreur(err.message);
      setEnvoi(false);
    }
  };

  return (
    <Modal titre={`Modifier « ${espace.nom} »`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-8">
        <fieldset className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <legend className="mb-3 text-sm font-bold uppercase tracking-wide text-fg-muted">Informations générales</legend>
          <Champ {...lie} nom="nom" label="Nom" required />
          <Champ {...lie} nom="ville" label="Ville" />
          <Champ {...lie} nom="surface_m2" label="Surface (m²)" type="number" min="0" step="any" />
        </fieldset>

        <fieldset className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <legend className="mb-3 text-sm font-bold uppercase tracking-wide text-fg-muted">Données agronomiques</legend>
          <Choix {...lie} nom="type_sol" label="Type de sol" options={TYPES_SOL} />
          <Champ {...lie} nom="ph_actuel" label="pH du sol" type="number" min="0" max="14" step="0.1" />
          <Choix {...lie} nom="exposition" label="Exposition" options={EXPOSITIONS} />
          <Choix {...lie} nom="drainage" label="Drainage" options={DRAINAGES} />
          <Champ {...lie} nom="humidite_cible" label="Humidité cible (%)" type="number" min="0" max="100" />
          <Champ {...lie} nom="frequence_arrosage_auto" label="Arrosage auto (heures)" type="number" min="0" />
          <Champ {...lie} nom="profondeur_racinaire" label="Profondeur racinaire (cm)" type="number" min="0" />
          <Champ {...lie} nom="reserve_utile_max" label="Réserve utile (mm)" type="number" min="1" step="any"
                 aide={espace.reserve_utile_max == null
                   ? `Calculée (FAO-56) : ${formatMm(espace.reserve_utile_effective_mm)} mm. Saisir une valeur pour la remplacer.`
                   : "Valeur saisie. Vider le champ pour revenir à la réserve calculée."} />
          <Champ {...lie} nom="coefficient_cultural" label="Coefficient paysager" type="number" min="0.1" max="3" step="0.05"
                 aide="0,8 pour un gazon." />
          <Choix {...lie} nom="type_irrigation" label="Irrigation" options={IRRIGATIONS}
                 aide="Efficacité retenue pour la dose : goutte-à-goutte 90 %, aspersion 75 %, manuel 70 %." />
          <Champ {...lie} nom="debit_arrosage_l_min" label="Débit d'arrosage (L/min)" type="number" min="0.1" step="any"
                 aide="Facultatif : donne la durée d'arrosage de la dose recommandée." />
          <Champ {...lie} nom="date_derniere_fertilisation" label="Dernière fertilisation" type="date" />
        </fieldset>

        {erreur && <Alert ton="danger">{erreur}</Alert>}

        <div className="flex flex-col gap-3 border-t border-line pt-5 sm:flex-row sm:items-center sm:justify-between">
          {confirmerSuppression ? (
            <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Confirmer la suppression">
              <span className="text-sm font-semibold text-danger">Supprimer définitivement cet espace et ses mesures ?</span>
              <Button variante="danger" taille="sm" onClick={supprimer} chargement={envoi}>Oui, supprimer</Button>
              <Button variante="fantome" taille="sm" onClick={() => setConfirmerSuppression(false)}>Non</Button>
            </div>
          ) : (
            <Button variante="fantome" icone={Trash2} onClick={() => setConfirmerSuppression(true)} className="text-danger hover:text-danger">
              Supprimer l'espace
            </Button>
          )}
          <div className="flex flex-col-reverse gap-3 sm:flex-row">
            <Button variante="secondaire" onClick={onClose}>Annuler</Button>
            <Button type="submit" chargement={envoi}>Enregistrer</Button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
