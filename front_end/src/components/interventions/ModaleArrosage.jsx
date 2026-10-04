import { useState } from "react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Field } from "../ui/Field";
import { Alert } from "../ui/Card";
import { nombreOuVide } from "../../lib/referentiels";

/**
 * Saisie du volume d'un arrosage (litres), pré-rempli et modifiable. Un arrosage terminé avec un volume
 * est compté aussitôt dans le bilan hydrique de l'espace (volume / surface).
 * `proposerTerminee` : case « déjà effectué » (création depuis le tableau de bord).
 */
export function ModaleArrosage({ titre, description, volumeInitial, aide, libelleValider, proposerTerminee = false,
                                 onValider, onClose }) {
  const [volume, setVolume] = useState(typeof volumeInitial === "number" ? String(volumeInitial) : "");
  const [terminee, setTerminee] = useState(!proposerTerminee);
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);

  const valider = async (e) => {
    e.preventDefault();
    setErreur("");
    setEnvoi(true);
    try {
      await onValider({ volume_eau_l: nombreOuVide(volume) ?? null, terminee });
    } catch (err) {
      setErreur(err.message);
      setEnvoi(false);
    }
  };

  return (
    <Modal titre={titre} description={description} onClose={onClose} largeur="max-w-lg">
      <form onSubmit={valider} className="space-y-5">
        <Field label="Volume d'eau (litres)" type="number" min="0" step="any" inputMode="decimal"
               value={volume} onChange={(e) => setVolume(e.target.value)} aide={aide} />
        {proposerTerminee && (
          <label className="flex items-start gap-3 text-sm text-fg-soft">
            <input type="checkbox" checked={terminee} onChange={(e) => setTerminee(e.target.checked)}
                   className="mt-0.5 h-4 w-4 accent-primary" />
            <span>
              Arrosage déjà effectué
              <span className="block text-xs text-fg-muted">Compté tout de suite dans le bilan de l'espace.</span>
            </span>
          </label>
        )}
        {erreur && <Alert ton="danger">{erreur}</Alert>}
        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button variante="secondaire" onClick={onClose}>Annuler</Button>
          <Button type="submit" chargement={envoi}>{libelleValider}</Button>
        </div>
      </form>
    </Modal>
  );
}
