# Design system GreenGuard

> Source : `front_end/src/index.css` (tokens) et `front_end/src/components/ui/` (composants).
> Cible d'accessibilité : **WCAG 2.1 AA**.

## 1. Règle d'or

Les composants n'utilisent **jamais** de couleur brute (`bg-slate-900`, `text-red-400`…) pour le
texte, les fonds ou les bordures. Ils utilisent les **tokens sémantiques** ci-dessous, qui changent
avec le thème. Exceptions tolérées : pictogrammes décoratifs (`text-teal-400`…), voiles de modale
(`bg-black/70`), boutons d'action colorés (bleu-600, orange-700, avec texte blanc ≥ 4,5:1).

## 2. Tokens

| Usage | Classe Tailwind | Clair | Sombre |
|---|---|---|---|
| Fond de page | `bg-canvas` | #f8fafc | #020617 |
| Carte, panneau | `bg-surface` | #ffffff | #0f172a |
| Survol, en-tête de tableau | `bg-surface-raised` | #f1f5f9 | #1e293b |
| Séparateur | `border-line` / `divide-line` | #e2e8f0 | #1e293b |
| Bordure de champ | `border-line-strong` | #cbd5e1 | #334155 |
| Texte principal | `text-fg` | #0f172a | #f8fafc |
| Texte secondaire | `text-fg-soft` | #334155 | #cbd5e1 |
| Texte d'aide, libellé discret | `text-fg-muted` | #475569 | #94a3b8 |
| Décoratif seulement | `text-fg-subtle` | #94a3b8 | #475569 |
| Action principale | `bg-primary` + `text-on-accent` | #15803d | #15803d |
| Contour de focus | `ring-focus` / `outline` | #15803d | #4ade80 |
| États | `text-success`, `text-danger`, `text-warning`, `text-info` | teintes 700-800 | teintes 400 |
| Fonds d'état | `bg-success-soft`, `bg-danger-soft`… | 8–10 % | 12 % |

Tous les textes atteignent au moins **4,5:1** sur `canvas`, `surface`, `surface-raised` **et sur leur propre fond teinté** (`*-soft`) dans les
deux thèmes (calculé lors de la phase 3). `text-fg-subtle` (≈ 2,5:1) est réservé au décor :
jamais pour une information.

## 3. Thème

`src/lib/theme.js` : `systeme` (par défaut, suit le système), `clair` ou `sombre`, mémorisé dans
le navigateur. Le thème est appliqué avant le premier rendu (`main.jsx`), via
`<html data-theme="light|dark">`. Choix dans **Paramètres**, ou par le bouton soleil/lune de l'en-tête.

## 4. Composants (`src/components/ui/`)

| Composant | Points clés |
|---|---|
| `Button` | Variantes `primaire`, `secondaire`, `fantome`, `danger` ; tailles `sm`, `md`, `lg` ; `chargement` (aria-busy). Bouton avec icône seule : `aria-label` obligatoire. |
| `Field` | Libellé relié au champ (`htmlFor`/`id`), aide et erreur reliées par `aria-describedby`, `aria-invalid`, astérisque si `required`. Pour un `<select>` : passer une fonction enfant qui reçoit les props d'accessibilité. |
| `Modal` | `role="dialog"`, `aria-modal`, titre relié, focus piégé, Échap et clic sur le voile pour fermer, focus rendu à l'élément d'origine. |
| `Card`, `Badge`, `Alert` | `Alert ton="danger"` est annoncé immédiatement (`role="alert"`), les autres tons poliment (`role="status"`). |
| `Logo`, `LogoMarque` | Marque unique « GreenGuard » (même dessin que `public/favicon.svg`). |

Référentiels partagés (types de sol, rôles, statuts) : `src/lib/referentiels.js`.
Hooks : `useTitrePage(titre)` (titre d'onglet) et `useRequete(charger)` (chargement annulable).

## 5. Règles d'accessibilité appliquées

- Langue `fr`, titre d'onglet propre à chaque page, un seul `<h1>` par page.
- Lien d'évitement « Aller au contenu », repères `nav` / `main` / `header`, fil d'Ariane avec `aria-current`.
- Taille de texte minimale : 12 px (`text-xs`).
- Focus visible partout (`:focus-visible`) ; préférence « réduire les animations » respectée.
- Pas de `div` cliquable : boutons ou liens, avec état (`aria-pressed`, `aria-expanded`, `aria-selected`).
- Images : texte alternatif, ou pictogramme `role="img"` avec libellé si la photo manque.
- Tableaux : `caption`, en-têtes `scope="col"`.
