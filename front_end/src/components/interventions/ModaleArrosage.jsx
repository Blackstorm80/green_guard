import { useState } from "react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Field } from "../ui/Field";
import { Alert } from "../ui/Card";
import { messageArrosage, nombreOuVide } from "../../lib/referentiels";

// Réalisation déclarée au plus 30 jours en arrière (au-delà, le serveur refuse : niveau VigiEau invérifiable)
const REALISATION_MAX_JOURS = 30;

/** Date → valeur d'un <input type="datetime-local"> (heure locale, à la minute). */
const versSaisieLocale = (date) => {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
};

/**
 * Saisie du volume d'un arrosage (litres), pré-rempli et modifiable. Un arrosage terminé avec un volume
 * est compté aussitôt dans le bilan hydrique de l'espace (volume / surface).
 * `proposerTerminee` : case « déjà effectué » (création depuis le tableau de bord).
 * `avertissement` : restriction sécheresse en vigueur, rappelée avant l'enregistrement. Un arrosage interdit
 * est refusé par le serveur (409) : son motif est affiché tel quel.
 * Arrosage effectué : sa date et son heure réelles (pré-remplies à maintenant) sont transmises en
 * `realisee_le` ; c'est à cette heure que la restriction est vérifiée et inscrite au registre sécheresse.
 */
export function ModaleArrosage({ titre, description, volumeInitial, aide, libelleValider, proposerTerminee = false,
                                 avertissement, onValider, onClose }) {
  const [volume, setVolume] = useState(typeof volumeInitial === "number" ? String(volumeInitial) : "");
  const [terminee, setTerminee] = useState(!proposerTerminee);
  const [ouverture] = useState(() => new Date());
  const [realiseeLe, setRealiseeLe] = useState(() => versSaisieLocale(ouverture));
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);

  const valider = async (e) => {
    e.preventDefault();
    setErreur("");
    let realisee_le;
    if (terminee) {
      const moment = new Date(realiseeLe);
      if (!realiseeLe || Number.isNaN(moment.getTime())) {
        setErreur("Indiquez la date et l'heure de l'arrosage.");
        return;
      }
      if (moment.getTime() > Date.now() + 60000) {
        setErreur("La date de l'arrosage ne peut pas être dans le futur.");
        return;
      }
      realisee_le = moment.toISOString();
    }
    setEnvoi(true);
    try {
      await onValider({ volume_eau_l: nombreOuVide(volume) ?? null, terminee, realisee_le });
    } catch (err) {
      setErreur(messageArrosage(err));
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
        {terminee && (
          <Field label="Date et heure de l'arrosage" type="datetime-local" required value={realiseeLe}
                 min={versSaisieLocale(new Date(ouverture.getTime() - REALISATION_MAX_JOURS * 86400000))}
                 onChange={(e) => setRealiseeLe(e.target.value)}
                 aide="Heure réelle de l'arrosage (pas celle de la saisie) : la restriction sécheresse est vérifiée à cette heure." />
        )}
        {avertissement && <Alert ton="alerte">{avertissement}</Alert>}
        {erreur && <Alert ton="danger">{erreur}</Alert>}
        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button variante="secondaire" onClick={onClose}>Annuler</Button>
          <Button type="submit" chargement={envoi}>{libelleValider}</Button>
        </div>
      </form>
    </Modal>
  );
}
