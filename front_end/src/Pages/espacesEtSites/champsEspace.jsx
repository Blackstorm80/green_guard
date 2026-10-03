import { Field } from "../../components/ui/Field";

/** Champ de saisie lié à un objet d'état `valeurs` via son `nom`. */
export function Champ({ nom, valeurs, onChange, ...props }) {
  return <Field name={nom} value={valeurs[nom] ?? ""} onChange={onChange} {...props} />;
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
