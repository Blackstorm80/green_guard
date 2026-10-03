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
  type_irrigation: espace?.type_irrigation ?? "",
  date_derniere_fertilisation: espace?.date_derniere_fertilisation ?? "",
});

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
          <Choix {...lie} nom="type_irrigation" label="Irrigation" options={IRRIGATIONS} />
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
