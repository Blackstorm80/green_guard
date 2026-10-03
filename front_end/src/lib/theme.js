/** Thème d'affichage : "clair", "sombre" ou "systeme" (suit la préférence du système d'exploitation). */
const CLE = "greenguard:theme";
/** Émis à chaque changement de thème appliqué (detail : "light" | "dark"). */
export const EVENEMENT_THEME = "greenguard:theme";
export const THEMES = ["systeme", "clair", "sombre"];

const requeteSombre = () => window.matchMedia("(prefers-color-scheme: dark)");

export function themeEnregistre() {
  try {
    const valeur = localStorage.getItem(CLE);
    return THEMES.includes(valeur) ? valeur : "systeme";
  } catch {
    return "systeme"; // stockage indisponible (navigation privée stricte…)
  }
}

export function appliquerTheme(choix = themeEnregistre()) {
  const sombre = choix === "sombre" || (choix === "systeme" && requeteSombre().matches);
  document.documentElement.dataset.theme = sombre ? "dark" : "light";
  window.dispatchEvent(new CustomEvent(EVENEMENT_THEME, { detail: sombre ? "dark" : "light" }));
}

export function enregistrerTheme(choix) {
  try {
    localStorage.setItem(CLE, choix);
  } catch {
    /* sans incidence : le choix vaut pour la session en cours */
  }
  appliquerTheme(choix);
}

/** À appeler une fois au démarrage : applique le thème et suit les changements de préférence système. */
export function initialiserTheme() {
  appliquerTheme();
  requeteSombre().addEventListener("change", () => {
    if (themeEnregistre() === "systeme") appliquerTheme("systeme");
  });
}
