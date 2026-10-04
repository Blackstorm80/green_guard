import { Field } from "../../components/ui/Field";
import { SOURCES_EAU } from "../../lib/referentiels";

/** Champ de saisie lié à un objet d'état `valeurs` via son `nom`. */
export function Champ({ nom, valeurs, onChange, ...props }) {
  return <Field name={nom} value={valeurs[nom] ?? ""} onChange={onChange} {...props} />;
}

/** Source d'eau de l'espace (mode sécheresse) : valeur obligatoire, réseau par défaut. */
export function ChoixSourceEau({ valeurs, onChange }) {
  return (
    <Field label="Source d'eau" aide="Détermine la zone d'alerte sécheresse (VigiEau) qui s'applique.">
      {(a11y) => (
        <select {...a11y} name="source_eau" value={valeurs.source_eau || "reseau"} onChange={onChange}>
          {Object.entries(SOURCES_EAU).map(([valeur, libelle]) => <option key={valeur} value={valeur}>{libelle}</option>)}
        </select>
      )}
    </Field>
  );
}

/** Liste déroulante accessible liée à `valeurs[nom]`. */
export function Choix({ nom, valeurs, onChange, options, label, ...props }) {
  return (
    <Field label={label} {...props}>
      {(a11y) => (
        <select {...a11y} name={nom} value={valeurs[nom] ?? ""} onChange={onChange}>
          <option value="">Non renseigné</option>
          {options.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      )}
    </Field>
  );
}
