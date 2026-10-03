import { cn } from "../../lib/utils";

const VARIANTES = {
  primaire: "bg-primary text-on-accent hover:bg-primary-hover",
  secondaire: "bg-surface-raised text-fg border border-line-strong hover:bg-surface-strong",
  fantome: "text-fg-muted hover:text-fg hover:bg-surface-raised",
  danger: "bg-red-700 text-on-accent hover:bg-red-800",
};
const TAILLES = {
  sm: "text-sm px-3 py-1.5 gap-1.5",
  md: "text-sm px-4 py-2.5 gap-2",
  lg: "text-base px-5 py-3 gap-2",
};

/** Bouton du design system. `icone` seule : fournir `aria-label`. */
export function Button({ variante = "primaire", taille = "md", icone: Icone, chargement = false,
                         className, children, disabled, type = "button", ...props }) {
  return (
    <button
      type={type}
      disabled={disabled || chargement}
      aria-busy={chargement || undefined}
      className={cn(
        "inline-flex items-center justify-center rounded-[var(--radius-control)] font-semibold transition-colors",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        VARIANTES[variante], TAILLES[taille], className
      )}
      {...props}
    >
      {Icone && <Icone size={taille === "sm" ? 14 : 18} aria-hidden />}
      {children}
    </button>
  );
}
