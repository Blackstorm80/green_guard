import { AlertTriangle, Ban, CheckCircle2, CircleHelp, Clock, Info } from "lucide-react";
import { Badge } from "../ui/Card";
import { NIVEAUX_VIGIEAU } from "../../lib/referentiels";

// Une forme par niveau, en plus de la couleur (WCAG 1.4.1)
const ICONES = {
  aucune: CheckCircle2, vigilance: Info, alerte: Clock, alerte_renforcee: AlertTriangle, crise: Ban, inconnu: CircleHelp,
};

/**
 * Niveau VigiEau du jour d'un espace (objet `secheresse` de l'API). `detail` : affiche aussi le motif
 * (ce que le niveau permet) et la dérogation éventuelle.
 */
export function PastilleVigieau({ secheresse, detail = false }) {
  if (!secheresse) return null;
  const { libelle, ton } = NIVEAUX_VIGIEAU[secheresse.niveau] ?? NIVEAUX_VIGIEAU.inconnu;
  const Icone = ICONES[secheresse.niveau] ?? CircleHelp;
  const pastille = (
    <Badge ton={ton}>
      <Icone size={12} aria-hidden /> <span>VigiEau : {libelle}</span>
    </Badge>
  );
  if (!detail) return <span title={secheresse.motif}>{pastille}</span>;
  return (
    <div className="flex flex-col gap-1">
      <div>{pastille}</div>
      <p className="text-xs text-fg-muted">
        {secheresse.motif}
        {secheresse.derogation && <> Dérogation : {secheresse.derogation.toLowerCase()}.</>}
        {secheresse.arrete_url && (
          <> <a href={secheresse.arrete_url} target="_blank" rel="noopener noreferrer"
                className="underline hover:text-fg">Voir l'arrêté</a></>
        )}
      </p>
    </div>
  );
}
