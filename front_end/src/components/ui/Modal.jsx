import { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";

const FOCUSABLES = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Boîte de dialogue modale accessible : role="dialog", titre relié, focus piégé dans la boîte,
 * fermeture par Échap ou clic sur le voile, focus rendu à l'élément d'origine à la fermeture.
 */
export function Modal({ titre, description, onClose, children, largeur = "max-w-2xl" }) {
  const refBoite = useRef(null);
  const idTitre = useId();
  const idDescription = useId();
  // Dernière version de onClose, sans relancer l'effet (sinon le focus sauterait à chaque rendu du parent)
  const refOnClose = useRef(onClose);
  useEffect(() => {
    refOnClose.current = onClose;
  });

  // Élément qui avait le focus à l'ouverture, capturé une seule fois
  // (en mode strict, React rejoue l'effet : la seconde capture viserait le champ de la modale)
  const refOrigine = useRef(null);

  useEffect(() => {
    refOrigine.current ??= document.activeElement;
    const origine = refOrigine.current;
    const boite = refBoite.current;
    // Premier champ de saisie en priorité (plutôt que le bouton Fermer)
    (boite?.querySelector("[data-autofocus], input:not([disabled]), select, textarea")
      ?? boite?.querySelector(FOCUSABLES))?.focus();
    document.body.style.overflow = "hidden";

    const surTouche = (e) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        refOnClose.current();
        return;
      }
      if (e.key !== "Tab" || !boite) return;
      const elements = [...boite.querySelectorAll(FOCUSABLES)];
      if (!elements.length) return;
      const premier = elements[0];
      const dernier = elements[elements.length - 1];
      if (e.shiftKey && document.activeElement === premier) {
        e.preventDefault();
        dernier.focus();
      } else if (!e.shiftKey && document.activeElement === dernier) {
        e.preventDefault();
        premier.focus();
      }
    };
    document.addEventListener("keydown", surTouche);
    return () => {
      document.removeEventListener("keydown", surTouche);
      document.body.style.overflow = "";
      origine?.focus?.();
    };
  }, []);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={refBoite}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitre}
        aria-describedby={description ? idDescription : undefined}
        className={`w-full ${largeur} max-h-[92vh] overflow-y-auto rounded-[var(--radius-card)] border border-line bg-surface p-6 shadow-2xl sm:p-8`}
      >
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h2 id={idTitre} className="text-xl font-bold text-fg">{titre}</h2>
            {description && <p id={idDescription} className="mt-1 text-sm text-fg-muted">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer"
            className="rounded-[var(--radius-control)] p-1.5 text-fg-muted hover:bg-surface-raised hover:text-fg"
          >
            <X size={22} aria-hidden />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
