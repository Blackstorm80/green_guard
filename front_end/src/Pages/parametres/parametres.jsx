import { useState } from "react";
import { LogOut, Monitor, Moon, Sun } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useTitrePage } from "../../lib/hooks";
import { enregistrerTheme, themeEnregistre } from "../../lib/theme";
import { LIBELLES_ROLES } from "../../lib/referentiels";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { cn } from "../../lib/utils";

const OPTIONS_THEME = [
  { valeur: "systeme", libelle: "Système", detail: "Suit le réglage de votre appareil", icone: Monitor },
  { valeur: "clair", libelle: "Clair", detail: "Fond clair en permanence", icone: Sun },
  { valeur: "sombre", libelle: "Sombre", detail: "Fond sombre en permanence", icone: Moon },
];

export default function Parametres() {
  useTitrePage("Paramètres");
  const { user, logout } = useAuth();
  const [theme, setTheme] = useState(themeEnregistre);

  const choisirTheme = (valeur) => {
    setTheme(valeur);
    enregistrerTheme(valeur);
  };

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-fg">Paramètres</h1>
        <p className="mt-1 text-fg-muted">Votre compte et vos préférences d'affichage.</p>
      </div>

      <Card aria-labelledby="titre-profil">
        <h2 id="titre-profil" className="text-lg font-semibold text-fg">Profil</h2>
        <dl className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <dt className="text-sm text-fg-muted">Nom</dt>
            <dd className="font-medium text-fg">{user?.name}</dd>
          </div>
          <div>
            <dt className="text-sm text-fg-muted">Adresse e-mail</dt>
            <dd className="break-all font-medium text-fg">{user?.email}</dd>
          </div>
          <div>
            <dt className="text-sm text-fg-muted">Rôle</dt>
            <dd className="font-medium text-fg">{LIBELLES_ROLES[user?.role] ?? user?.role}</dd>
          </div>
        </dl>
      </Card>

      <Card aria-labelledby="titre-apparence">
        <fieldset>
          <legend id="titre-apparence" className="text-lg font-semibold text-fg">Apparence</legend>
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
            {OPTIONS_THEME.map(({ valeur, libelle, detail, icone: Icone }) => (
              <label
                key={valeur}
                className={cn(
                  "flex cursor-pointer items-start gap-3 rounded-[var(--radius-control)] border p-4 transition-colors",
                  "has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-focus",
                  theme === valeur ? "border-primary bg-success-soft" : "border-line hover:bg-surface-raised"
                )}
              >
                <input type="radio" name="theme" value={valeur} checked={theme === valeur}
                       onChange={() => choisirTheme(valeur)} className="sr-only" />
                <Icone size={20} aria-hidden className="mt-0.5 text-fg-muted" />
                <span>
                  <span className="block font-semibold text-fg">{libelle}</span>
                  <span className="block text-sm text-fg-muted">{detail}</span>
                </span>
              </label>
            ))}
          </div>
        </fieldset>
      </Card>

      <Card aria-labelledby="titre-session">
        <h2 id="titre-session" className="text-lg font-semibold text-fg">Session</h2>
        <p className="mt-2 text-sm text-fg-muted">
          Votre session est conservée dans un cookie sécurisé et expire automatiquement au bout de 60 minutes.
        </p>
        <Button variante="secondaire" icone={LogOut} onClick={logout} className="mt-4">Se déconnecter</Button>
      </Card>

      <p className="text-xs text-fg-muted">GreenGuard · version 0.9 (pré-version)</p>
    </div>
  );
}
