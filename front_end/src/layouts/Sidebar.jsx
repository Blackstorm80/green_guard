import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { FileText, LayoutDashboard, LogOut, Menu, Settings, Sprout, Trees, X } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { cn } from "../lib/utils";
import { Logo } from "../components/ui/Logo";
import { LIBELLES_ROLES } from "../lib/referentiels";

const NAVIGATION = [
  { name: "Tableau de bord", href: "/dashboard", icon: LayoutDashboard },
  { name: "Espaces et zones", href: "/espaces", icon: Trees },
  { name: "Catalogue", href: "/catalogues", icon: Sprout },
  { name: "Rapports", href: "/rapports", icon: FileText },
  { name: "Paramètres", href: "/parametres", icon: Settings },
];

const initiales = (texte) => {
  if (!texte) return "?";
  const mots = texte.trim().split(/\s+/);
  return (mots.length > 1 ? `${mots[0][0]}${mots[1][0]}` : texte.slice(0, 2)).toUpperCase();
};

export function Sidebar() {
  const [ouvert, setOuvert] = useState(false);
  const { user, logout } = useAuth();

  // Échap ferme le menu mobile
  useEffect(() => {
    if (!ouvert) return undefined;
    const surTouche = (e) => e.key === "Escape" && setOuvert(false);
    document.addEventListener("keydown", surTouche);
    return () => document.removeEventListener("keydown", surTouche);
  }, [ouvert]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOuvert(!ouvert)}
        aria-label={ouvert ? "Fermer le menu" : "Ouvrir le menu"}
        aria-expanded={ouvert}
        aria-controls="menu-principal"
        className="fixed left-4 top-3 z-50 rounded-[var(--radius-control)] border border-line bg-surface p-2 text-fg shadow-lg lg:hidden"
      >
        {ouvert ? <X size={22} aria-hidden /> : <Menu size={22} aria-hidden />}
      </button>

      <aside
        id="menu-principal"
        className={cn(
          "sidebar fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-line bg-surface transition-transform duration-300 lg:translate-x-0",
          ouvert ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center border-b border-line px-6">
          <Logo compact />
        </div>

        <nav aria-label="Navigation principale" className="flex-1 space-y-1 overflow-y-auto p-4">
          {NAVIGATION.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              onClick={() => setOuvert(false)}
              className={({ isActive }) => cn(
                "flex items-center rounded-[var(--radius-control)] px-4 py-3 text-sm font-medium transition-colors",
                isActive ? "bg-success-soft font-semibold text-success" : "text-fg-muted hover:bg-surface-raised hover:text-fg"
              )}
            >
              <item.icon className="mr-3 h-5 w-5" aria-hidden />
              {item.name}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-line p-4">
          <div className="flex items-center gap-3 p-2">
            <div aria-hidden className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-on-accent">
              {initiales(user?.name || user?.email)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-fg">{user?.name || user?.email}</p>
              <p className="truncate text-xs text-fg-muted">{LIBELLES_ROLES[user?.role] ?? user?.role}</p>
            </div>
            <button
              type="button"
              onClick={logout}
              aria-label="Se déconnecter"
              title="Se déconnecter"
              className="rounded-[var(--radius-control)] p-2 text-fg-muted transition-colors hover:bg-danger-soft hover:text-danger"
            >
              <LogOut size={18} aria-hidden />
            </button>
          </div>
        </div>
      </aside>

      {ouvert && (
        <div aria-hidden className="fixed inset-0 z-30 bg-black/60 lg:hidden" onClick={() => setOuvert(false)} />
      )}
    </>
  );
}
