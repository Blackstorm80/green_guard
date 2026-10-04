# Rapport de recette — GreenGuard 1.0.0-rc1

**Date** : 2026-10-04 · **Branche** : `release/v1.0.0-rc1` · **Tag** : `v1.0.0-rc1` (local)
**Verdict** : ✅ **Version candidate acceptée, avec deux réserves** (performance à confirmer sur
l'hébergement cible ; actions de sécurité à mener par le porteur de projet avant la mise en ligne).

## 1. Environnements

| Environnement | Composition | Usage |
|---|---|---|
| Recette isolée | PostgreSQL 16 jetable (port 55432), API uvicorn 1 processus (8100), build de production du front servi par `vite preview` (4173) | Tests de bout en bout, test de charge |
| Pile Docker locale | `docker compose -p greenguard` : db, backend, worker, frontend (nginx) | Vérifications visuelles, sauvegarde et restauration |
| CI (GitHub Actions) | Pile `docker compose` complète | Rejoue tout à chaque PR (non encore exécutée : branche non poussée) |

Poste de mesure : ordinateur portable Windows faisant tourner en même temps le générateur de charge,
PostgreSQL, l'API, le front et la pile Docker locale.

## 2. Résultats

| Contrôle | Résultat |
|---|---|
| Tests back (pytest, SQLite et PostgreSQL 16) | ✅ 70/70, couverture 96 % |
| Migrations Alembic (upgrade, absence de dérive, downgrade) sur PostgreSQL | ✅ |
| Lint back (ruff, dont règles de sécurité bandit) et front (ESLint) | ✅ 0 erreur |
| Tests de bout en bout Playwright, bureau et mobile, sur le build de production | ✅ 20/20 |
| Audit d'accessibilité axe-core WCAG 2.1 A/AA, 7 pages + modale, thèmes clair et sombre | ✅ 0 violation sérieuse ou critique |
| Scan de secrets gitleaks sur HEAD | ✅ aucune fuite |
| Audit des dépendances (pip-audit, npm audit) | ✅ 0 vulnérabilité |
| Sauvegarde puis restauration dans une base temporaire | ✅ 8 tables identiques, révision `0001_schema_v1` |
| Garde-fous de restauration (production sans confirmation, nom de base piégé) | ✅ refusés |
| Test de charge (voir § 3) | ⚠️ réserve sur un indicateur |

### Parcours couverts par les tests de bout en bout
Route protégée vers la connexion ; identifiants incorrects ; inscription → tableau de bord vide →
déconnexion (cookie httpOnly vérifié, aucune donnée de session lisible en JavaScript) ; création,
modification et suppression d'un espace via les modales ; fermeture d'une modale par Échap avec
restitution du focus ; persistance du thème ; page 404.

## 3. Test de charge (200 espaces, 200 requêtes par route, 20 simultanées)

`back_end/scripts/charge/test_charge.py`, API à **un seul processus**.

| Mesure | Résultat | Seuil | |
|---|---|---|---|
| Job horaire (200 bilans, mesures, notifications, vraie météo) | 9,4 à 13,7 s | < 60 s | ✅ |
| Recalcul des zones intelligentes | 1,7 à 2,9 s | — | ✅ |
| `GET /espaces-verts/` p95 | 388 à 467 ms | < 500 ms | ✅ |
| `GET /zones/` p95 | 241 à 273 ms | < 500 ms | ✅ |
| `GET /interventions/urgent` p95 | 245 à 253 ms | < 500 ms | ✅ |
| `GET /capteurs/dashboard` p50 / p95 | 232 ms / 540 à 660 ms | p95 < 500 ms | ⚠️ |
| Erreurs | 0 | 0 | ✅ |

**Réserve n° 1** : le p95 du tableau de bord dépasse le seuil sur le poste de mesure, qui fait
tourner tout le reste en même temps. Le débit (65 à 71 req/s) correspond à plus de 2 000 personnes
consultant simultanément le tableau de bord, rafraîchi toutes les 30 s. Rejouer le script sur
l'hébergement retenu (décision D-7) et ajuster `WEB_CONCURRENCY` avant la mise en production.

## 4. Défauts trouvés pendant la recette (tous corrigés)

| Gravité | Défaut | Correction |
|---|---|---|
| 🔴 Critique | **Interblocage de l'API** dès 20 requêtes simultanées : dépendance d'authentification `async` faisant des requêtes SQL synchrones sur la boucle d'événements ; pool épuisé, plus aucune réponse (même la connexion) | Dépendance synchrone, pool dimensionné et configurable, test de non-régression |
| 🟠 Majeur | `GET /espaces-verts/` à 3,3 s (une requête par espace pour `zone_id`) | Chargement groupé : 0,3 s |
| 🟠 Majeur | Conteneur front « unhealthy » en permanence (sonde IPv6, nginx IPv4) : redémarrages en boucle sous un orchestrateur | nginx en IPv4 + IPv6, sonde sur 127.0.0.1 |
| 🟠 Majeur | Contraste insuffisant en thème clair : vert (4,13:1) et ambre (4,14:1) sur fond teinté | Teintes foncées (5,8:1) |
| 🟡 Mineur | Bouton mobile « Ajouter un espace » rétrécissant et regrandissant en boucle, sans respect de « réduire les animations » | Bouton simple, halo CSS ; framer-motion retiré (bundle −27 %) |
| 🟡 Mineur | Tableau de bord : 20 appels météo identiques quand le cache est vide | Un seul appel par point |
| 🟡 Mineur | `npm run lint` en échec sur la configuration Playwright ; faux positifs gitleaks sur les clés de test de la CI | Corrigés (la CI aurait échoué) |

## 5. Revue de sécurité : risques résiduels acceptés pour la v1

| Risque | Évaluation | Suite |
|---|---|---|
| Jeton JWT valable jusqu'à expiration (60 min) même après déconnexion, s'il a été dérobé | Faible : cookie httpOnly, CSP, pas de stockage navigateur | Liste de révocation (`jti`) après la v1 si nécessaire |
| L'inscription révèle qu'un e-mail existe (400 au lieu de 201) | Faible, courant | Message générique déjà en place ; vérification par e-mail après la v1 |
| Limitation de débit en mémoire : par processus | Faible avec 1 processus | Redis si plusieurs instances |
| Processus maître nginx en root dans l'image front | Faible (fichiers statiques) | Image `nginx-unprivileged` après la v1 |
| Pas de réinitialisation de mot de passe | Fonctionnel | Création par un administrateur (`create_user.py`) en attendant |

**Réserve n° 2, à traiter AVANT la mise en ligne** (porteur de projet) :
1. Révoquer les 2 clés OpenWeather et changer les mots de passe des 2 comptes admin qui figuraient
   dans la base SQLite publiée.
2. Purger l'historique git (3 fuites anciennes encore présentes : `.env`, `weatherServices.js`, `meteo.py`).
3. Activer la protection de `main`, le secret scanning et la push protection sur GitHub.

## 6. Décisions encore ouvertes

| # | Sujet | Impact |
|---|---|---|
| D-4 | Validation agronomique des seuils de stress et des facteurs de sol | Fiabilité des recommandations d'arrosage |
| D-6 | Périmètre de la page Rapports (version minimale livrée) | Fonctionnel |
| D-7 | Hébergement de production | HTTPS, domaine, sauvegardes hors serveur, réserve n° 1 |
