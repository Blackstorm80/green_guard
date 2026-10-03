import { useState } from "react";
import { api } from "../../services/api";
import { Modal } from "../../components/ui/Modal";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Card";
import { Champ, Choix } from "./champsEspace";
import { nombreOuVide, TYPES_ESPACE, TYPES_SOL } from "../../lib/referentiels";

const INITIAL = {
  nom: "", type_espace: "Parc", ville: "", latitude: "", longitude: "",
  surface_m2: "", type_sol: "Argileux", ph_actuel: "7", reserve_utile_max: "100", coefficient_cultural: "0.8",
};

export default function AddSpaceModal({ onClose, onSuccess }) {
  const [valeurs, setValeurs] = useState(INITIAL);
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const onChange = (e) => setValeurs((v) => ({ ...v, [e.target.name]: e.target.value }));
  const lie = { valeurs, onChange };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErreur("");
    setEnvoi(true);
    try {
      // Le propriétaire est déduit de la session côté serveur : aucun user_id envoyé
      await api.createEspace({
        nom: valeurs.nom.trim(),
        type_espace: valeurs.type_espace || undefined,
        ville: valeurs.ville.trim() || undefined,
        type_sol: valeurs.type_sol || undefined,
        latitude: Number(valeurs.latitude),
        longitude: Number(valeurs.longitude),
        surface_m2: nombreOuVide(valeurs.surface_m2),
        ph_actuel: nombreOuVide(valeurs.ph_actuel),
        reserve_utile_max: nombreOuVide(valeurs.reserve_utile_max),
        coefficient_cultural: nombreOuVide(valeurs.coefficient_cultural),
      });
      onSuccess();
      onClose();
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <Modal titre="Nouvel espace vert" description="Les champs marqués d'un astérisque sont obligatoires." onClose={onClose} largeur="max-w-3xl">
      <form onSubmit={handleSubmit} className="space-y-8">
        <fieldset className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <legend className="mb-3 text-sm font-bold uppercase tracking-wide text-fg-muted">Identité et localisation</legend>
          <Champ {...lie} nom="nom" label="Nom de l'espace" required className="md:col-span-2" />
          <Choix {...lie} nom="type_espace" label="Type d'espace" options={TYPES_ESPACE} />
          <Champ {...lie} nom="ville" label="Ville ou commune" />
          <Champ {...lie} nom="latitude" label="Latitude" type="number" step="any" min="-90" max="90" required aide="Ex. 45.764" />
          <Champ {...lie} nom="longitude" label="Longitude" type="number" step="any" min="-180" max="180" required aide="Ex. 4.835" />
        </fieldset>

        <fieldset className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <legend className="mb-3 text-sm font-bold uppercase tracking-wide text-fg-muted">Agronomie</legend>
          <Champ {...lie} nom="surface_m2" label="Surface (m²)" type="number" min="0" step="any" />
          <Choix {...lie} nom="type_sol" label="Type de sol" options={TYPES_SOL} />
          <Champ {...lie} nom="ph_actuel" label="pH du sol" type="number" min="0" max="14" step="0.1" />
          <Champ {...lie} nom="reserve_utile_max" label="Réserve utile max (mm)" type="number" min="1" step="any"
                 aide="Eau disponible pour les plantes, sol plein." />
          <Champ {...lie} nom="coefficient_cultural" label="Coefficient cultural" type="number" min="0.1" max="3" step="0.05"
                 aide="Besoin en eau relatif de la végétation (Kc)." />
        </fieldset>

        {erreur && <Alert ton="danger">{erreur}</Alert>}

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button variante="secondaire" onClick={onClose}>Annuler</Button>
          <Button type="submit" chargement={envoi}>{envoi ? "Enregistrement…" : "Enregistrer l'espace"}</Button>
        </div>
      </form>
    </Modal>
  );
}
