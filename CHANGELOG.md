# Journal des versions

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) ; versions selon [SemVer](https://semver.org/lang/fr/).

## [Non publié]

### Ajouté
- Multi-organisations : une instance sert plusieurs collectivités cloisonnées ; les agents d'une même
  organisation partagent son patrimoine. Rôles `admin`, `gestionnaire`, `technicien`, `lecteur` (élu, lecture
  seule) appliqués à toutes les routes d'écriture ; administrateur de la plateforme (`est_superadmin`).
- Routes `/organisations/moi` (nom, paramètres métier), `/organisations/moi/membres` (rôle, désactivation ;
  dernier admin protégé) et `POST /organisations` (superadmin). `create_user.py --organisation --role --superadmin`.
- Front : nom de l'organisation dans la barre latérale, gestion des membres dans Paramètres, actions
  masquées selon le rôle ; champ facultatif « collectivité » à l'inscription.

### Modifié
- Migration `0002_organisations` : « Organisation par défaut » pour les données existantes ; rôles
  `manager` et `user` → `gestionnaire` ; l'ancien propriétaire d'un espace devient son créateur (`cree_par`).
- L'inscription crée une nouvelle organisation dont le compte est administrateur (provisoire, avant l'invitation).
- `GET /espaces-verts` : `user_id` remplacé par `organisation_id` et `cree_par`.
- `/vegetal/*` : ouvert au gestionnaire, limité au patrimoine de son organisation (et non plus à toute la base).
- Alerte de stress critique envoyée aux membres actifs qui interviennent (admin, gestionnaire, technicien).

### Sécurité
- Isolation par la base (PostgreSQL) : Row Level Security forcée sur les tables métier, contexte
  d'organisation reposé à chaque transaction ; avertissement au démarrage si le rôle de connexion
  l'ignore (superutilisateur).
- API et front publiés sur `127.0.0.1` par défaut (`API_BIND`, `FRONT_BIND`) : en production, seul le
  reverse proxy TLS y accède.
- Proxys de confiance configurables (`TRUSTED_PROXIES` → `--forwarded-allow-ips`) ; connexion limitée par
  identifiant (`AUTH_RATE_LIMIT`) et par IP (`AUTH_RATE_LIMIT_IP`, 100) : 10 mauvais mots de passe ne
  bloquent plus toute une collectivité derrière la même IP.
- Documentation interactive fermée par défaut (`ENABLE_DOCS=false` : `/docs`, `/redoc`, `/openapi.json` en 404).

### Corrigé
- Jour du bilan hydrique calculé dans le fuseau métier (`FUSEAU_HORAIRE`, Europe/Paris) et non en UTC,
  comme les cumuls météo Open-Meteo : entre 0 h et 2 h, le bilan de la veille n'est plus écrasé.
- Impact carbone : facteur sourcé (Nowak & Crane, 2002 : ≈ 1,12 kg CO₂/m²/an, majorant) au lieu
  d'environ 18 kg/m²/an ; l'API indique `estimation_grossiere` et `methode`. Le détail par zone est
  désormais projeté sur l'année, comme les totaux.

## [1.0.0-rc1] — 2026-10-04 (version candidate)

Première version candidate après la reprise du projet. Plan et décisions :
`PLAN_ARCHITECTE_2026-10-03.md` ; rapport de recette : `documentation/recette_v1.0.0-rc1.md`.

### Sécurité
- Secrets retirés du code et des fichiers versionnés (clé OpenWeather, secret JWT, base SQLite
  contenant des comptes) ; scan de secrets en CI. **Rotation des clés et purge de l'historique
  restent à faire** (voir le guide d'exploitation).
- Session par cookie `httpOnly` + `SameSite=Lax` + `Secure`, protection CSRF, PyJWT (remplace
  python-jose), limitation de débit sur la connexion et l'inscription, mot de passe de 12 caractères
  minimum, `SECRET_KEY` de 32 caractères minimum.
- Isolation stricte entre comptes (plusieurs accès aux données d'autres utilisateurs corrigés),
  plus d'escalade de privilèges à l'inscription, comptes désactivés bloqués immédiatement.
- En-têtes de sécurité et CSP sur l'API et le front, erreurs 500 génériques, images Docker non root.
- Dépendances : CVE corrigées (PyJWT, python-multipart, python-dotenv, requests, react-router,
  postcss…) ; pip-audit et npm audit à zéro.

### Corrigé
- API réellement fonctionnelle : préfixes de routes doublés, une dizaine de routes en erreur 500,
  modules qui ne s'importaient pas, création et édition d'espace impossibles côté front.
- Bilan hydrique : la réserve en eau était décomptée à chaque passage du job (720 fois par jour) ;
  calcul journalier idempotent à partir de la météo réelle.
- Interblocage de l'API sous charge (dépendance `async` bloquant la boucle d'événements) ; requêtes
  N+1 sur les espaces, le tableau de bord et les zones.
- Clustering : centroïdes enregistrés en coordonnées normalisées (fausses positions).
- Données inventées supprimées (valeurs aléatoires, O₂ constant, notifications et rapports factices).
- Conteneur front marqué « unhealthy » en permanence ; bouton mobile animé en boucle.

### Ajouté
- Schéma PostgreSQL v1 piloté par Alembic : contraintes d'intégrité, cascades, index, dates avec fuseau.
- Service worker dédié aux tâches planifiées ; notifications de stress hydrique critique.
- CRUD des interventions (repris de la branche de Lucresse) ; boutons d'action du tableau de bord.
- Page Rapports (historique réel, filtres, export CSV, impression) ; page Paramètres.
- Design system (tokens sémantiques, thèmes clair et sombre), accessibilité WCAG 2.1 AA vérifiée
  par audit automatique (axe-core).
- Catalogue iNaturalist rechargé proprement (1 258 plantes, 80 auxiliaires).
- Tests : 70 tests back (96 % de couverture, SQLite et PostgreSQL), 20 tests de bout en bout
  Playwright (bureau et mobile) ; CI complète ; test de charge ; scripts de sauvegarde et restauration.

### Retiré
- Environ 80 fichiers de code mort ou cassé ; `node_modules`, `dist/` et la base SQLite du dépôt ;
  dépendances inutilisées (passlib, python-jose, python-weather, websockets, framer-motion).

### Notes de migration
- Toute base de développement créée avant octobre 2026 doit être recréée (`docker compose down -v`) :
  la migration de référence a été remplacée par `0001_schema_v1`.
- Nouvelles variables d'environnement : voir `.env.example` et `documentation/Doc_back_end.md`.
