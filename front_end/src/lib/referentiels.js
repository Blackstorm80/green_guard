/** Référentiels partagés (listes de valeurs et libellés), séparés des composants pour le Fast Refresh. */

export const TYPES_ESPACE = ["Parc", "Jardin", "Square", "Toiture", "Rue"];
export const TYPES_SOL = ["Argileux", "Limoneux", "Limon-Argileux", "Sableux"];
export const EXPOSITIONS = ["Soleil", "Mi-ombre", "Ombre"];
export const DRAINAGES = ["Faible", "Moyen", "Bon"];
export const IRRIGATIONS = ["Goutte-à-goutte", "Aspersion", "Manuel", "Aucune"];

export const LIBELLES_ROLES = {
  admin: "Administrateur",
  gestionnaire: "Gestionnaire",
  technicien: "Technicien",
  lecteur: "Lecteur",
};
export const ROLES = Object.keys(LIBELLES_ROLES);

/**
 * Droits renvoyés par /users/me (le serveur reste seul juge) : « interventions » (technicien et plus),
 * « gestion » (espaces, zones, paramètres : gestionnaire et admin), « membres » (admin).
 */
export const peut = (user, permission) => Boolean(user?.permissions?.includes(permission));

/** Statut hydrique → ton de badge. */
export const TON_STATUT = {
  Optimal: "succes",
  "A surveiller": "alerte",
  Critique: "danger",
  "Sans donnée": "neutre",
};

// Décision de la prévision à 7 jours (tableau de bord)
export const DECISIONS_PREVISION = {
  arroser: { libelle: "Arroser", ton: "danger" },
  reporter: { libelle: "Reporter", ton: "info" },
  surveiller: { libelle: "À surveiller", ton: "alerte" },
  rien: { libelle: "Rien à prévoir", ton: "succes" },
  interdit: { libelle: "Arrosage interdit", ton: "danger" },
};

// Mode sécheresse : niveau VigiEau du jour (PastilleVigieau double la couleur d'une icône, pour l'accessibilité)
export const NIVEAUX_VIGIEAU = {
  aucune: { libelle: "Aucune restriction", ton: "succes" },
  vigilance: { libelle: "Vigilance", ton: "info" },
  alerte: { libelle: "Alerte", ton: "alerte" },
  alerte_renforcee: { libelle: "Alerte renforcée", ton: "danger" },
  crise: { libelle: "Crise", ton: "danger" },
  inconnu: { libelle: "Niveau inconnu", ton: "neutre" },
};

// Ressource prélevée : elle détermine la zone d'alerte VigiEau (eau potable, nappe, cours d'eau)
export const SOURCES_EAU = {
  reseau: "Réseau d'eau potable",
  forage: "Forage (nappe)",
  riviere: "Rivière ou canal",
  recuperation: "Eau de récupération",
};

/** Message d'un refus d'arrosage par l'arrêté sécheresse (409), sinon le message d'origine. */
export const messageArrosage = (err) =>
  err?.status === 409 ? `Arrosage refusé (arrêté sécheresse). ${err.message}` : err?.message;

export const LIBELLES_INTERVENTION = {
  arrosage: "Arrosage", ombrage: "Ombrage", taille: "Taille", fertilisation: "Fertilisation",
  traitement: "Traitement", nettoyage: "Nettoyage", diagnostic: "Diagnostic",
};
export const LIBELLES_STATUT_INTERVENTION = { planifiee: "Planifiée", en_cours: "En cours", terminee: "Terminée" };

/** Valeur saisie → nombre, ou undefined si le champ est vide (le champ est alors omis du payload). */
export const nombreOuVide = (valeur) => (valeur === "" || valeur === null || valeur === undefined ? undefined : Number(valeur));

/** Aujourd'hui (heure locale) au format d'un <input type="date"> : borne haute de la date de plantation. */
export const aujourdhuiSaisie = () => {
  const maintenant = new Date();
  return new Date(maintenant.getTime() - maintenant.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
};
