import { cn } from "../../lib/utils";

export function Card({ as: Balise = "section", className, children, ...props }) {
  return (
    <Balise className={cn("rounded-[var(--radius-card)] border border-line bg-surface p-5 sm:p-6", className)} {...props}>
      {children}
    </Balise>
  );
}

const TONS = {
  neutre: "bg-surface-raised text-fg-soft",
  succes: "bg-success-soft text-success",
  danger: "bg-danger-soft text-danger",
  alerte: "bg-warning-soft text-warning",
  info: "bg-info-soft text-info",
};

export function Badge({ ton = "neutre", className, children }) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold", TONS[ton], className)}>
      {children}
    </span>
  );
}

/** Message d'état. `ton="danger"` est annoncé immédiatement aux lecteurs d'écran (role="alert"). */
export function Alert({ ton = "info", className, children }) {
  const bordure = { danger: "border-danger-line", succes: "border-success/30", alerte: "border-warning/40", info: "border-info/30" };
  return (
    <div
      role={ton === "danger" ? "alert" : "status"}
      className={cn("rounded-[var(--radius-control)] border p-3 text-sm font-medium", TONS[ton], bordure[ton], className)}
    >
      {children}
    </div>
  );
}
