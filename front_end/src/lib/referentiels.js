/** Référentiels partagés (listes de valeurs et libellés), séparés des composants pour le Fast Refresh. */

export const TYPES_ESPACE = ["Parc", "Jardin", "Square", "Toiture", "Rue"];
export const TYPES_SOL = ["Argileux", "Limoneux", "Limon-Argileux", "Sableux"];
export const EXPOSITIONS = ["Soleil", "Mi-ombre", "Ombre"];
export const DRAINAGES = ["Faible", "Moyen", "Bon"];
export const IRRIGATIONS = ["Goutte-à-goutte", "Aspersion", "Manuel", "Aucune"];

export const LIBELLES_ROLES = { admin: "Administrateur", manager: "Gestionnaire", user: "Utilisateur" };

/** Statut hydrique → ton de badge. */
export const TON_STATUT = {
  Optimal: "succes",
  "A surveiller": "alerte",
  Critique: "danger",
  "Sans donnée": "neutre",
};

export const LIBELLES_INTERVENTION = {
  arrosage: "Arrosage", ombrage: "Ombrage", taille: "Taille", fertilisation: "Fertilisation",
  traitement: "Traitement", nettoyage: "Nettoyage", diagnostic: "Diagnostic",
};
export const LIBELLES_STATUT_INTERVENTION = { planifiee: "Planifiée", en_cours: "En cours", terminee: "Terminée" };

/** Valeur saisie → nombre, ou undefined si le champ est vide (le champ est alors omis du payload). */
export const nombreOuVide = (valeur) => (valeur === "" || valeur === null || valeur === undefined ? undefined : Number(valeur));
