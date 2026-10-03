import { useId } from "react";
import { cn } from "../../lib/utils";

const CONTROLE = cn(
  "w-full rounded-[var(--radius-control)] border border-line-strong bg-surface px-3 py-2.5 text-fg",
  "placeholder:text-fg-muted focus:border-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-focus/40",
  "aria-[invalid=true]:border-danger"
);

/**
 * Champ de formulaire accessible : libellé associé (htmlFor/id), aide et erreur reliées par aria-describedby.
 * `children` (optionnel) : un <select> ou un contrôle personnalisé recevant les props d'accessibilité.
 */
export function Field({ label, aide, erreur, icone: Icone, className, children, id, ...props }) {
  const autoId = useId();
  const idChamp = id ?? autoId;
  const idAide = aide ? `${idChamp}-aide` : undefined;
  const idErreur = erreur ? `${idChamp}-erreur` : undefined;
  const accessibilite = {
    id: idChamp,
    "aria-describedby": [idAide, idErreur].filter(Boolean).join(" ") || undefined,
    "aria-invalid": erreur ? true : undefined,
  };

  return (
    <div className={cn("space-y-1.5", className)}>
      <label htmlFor={idChamp} className="block text-sm font-semibold text-fg-soft">
        {label}
        {props.required && <span className="text-danger" aria-hidden> *</span>}
      </label>
      <div className="relative">
        {Icone && <Icone size={18} aria-hidden className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-fg-muted" />}
        {children
          ? children({ ...accessibilite, className: cn(CONTROLE, Icone && "pl-10") })
          : <input {...accessibilite} className={cn(CONTROLE, Icone && "pl-10")} {...props} />}
      </div>
      {aide && <p id={idAide} className="text-xs text-fg-muted">{aide}</p>}
      {erreur && <p id={idErreur} className="text-xs font-semibold text-danger">{erreur}</p>}
    </div>
  );
}
