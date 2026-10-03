import { cn } from "../../lib/utils";

/** Marque GreenGuard : bouclier + feuille. Même dessin que public/favicon.svg. */
export function LogoMarque({ taille = 40, className }) {
  return (
    <svg width={taille} height={taille} viewBox="0 0 32 32" aria-hidden className={className}>
      <path d="M16 2 4 6.5v8.2c0 7.3 5 13.3 12 15.3 7-2 12-8 12-15.3V6.5L16 2Z" fill="#15803d" />
      <path d="M21.5 10.5c-6.2 0-10 3.2-10 8.3 0 1.2.3 2.3.8 3.2 1-3.4 3.4-5.8 6.7-7.1-2.8 1.8-4.7 4.3-5.4 7.6.9.5 1.9.7 3 .7 4.6 0 6.5-4.2 4.9-12.7Z" fill="#ffffff" />
    </svg>
  );
}

export function Logo({ className, compact = false }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMarque taille={compact ? 28 : 36} />
      <span className={cn("font-extrabold tracking-tight text-fg", compact ? "text-lg" : "text-2xl")}>
        Green<span className="text-success">Guard</span>
      </span>
    </span>
  );
}
