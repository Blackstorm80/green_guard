# GreenGuard : audit de reprise et plan d'action jusqu'à la v1.0

**Date** : 2026-10-03
**Rôle** : architecte logiciel (reprise du projet)
**Périmètre** : front (React/Vite), back (FastAPI), BDD (SQLAlchemy/Alembic/PostgreSQL), infra (Docker, CI), dépôt git, design/UX
**Méthode** : lecture intégrale du code, import et appel de chaque route avec TestClient sur une BDD temporaire, `npm run lint` et `npm run build`, `pytest`, inspection de l'historique git et de la BDD SQLite versionnée.

> **Sortie officielle v1.0 fixée au mardi 1er décembre 2026.** Gel des fonctionnalités le 20 novembre, recette du 23 au 27 novembre.

---

## 1. Verdict

**État : 🔴 non livrable en l'état.** L'architecture visée (Onion) est bonne et le métier a de la valeur : bilan hydrique, stress, zones intelligentes. Mais trois problèmes s'additionnent.

1. **Ce qui est publié sur GitHub reste compromis.** Les correctifs de sécurité de juin 2026 n'ont **jamais été commités** : ils n'existent que dans la copie de travail locale. `origin/main` contient encore la clé OpenWeather, le secret JWT écrit en dur dans le code, et une base SQLite avec **2 comptes `admin` (emails nominatifs et hash bcrypt)**.
2. **L'application ne fonctionne pas de bout en bout.** Les routes ont un préfixe doublé (`/api/v1/auth/auth/login`, `/api/v1/meteo/meteo/...`), environ 10 routes renvoient une 500, et le front appelle 4 fonctions qui n'existent pas dans `api.js` (création et édition d'espace impossibles). Le dashboard affiche des KPI vides, et le job planifié plante à chaque exécution sans que personne ne le sache.
3. **Le document `ETAT_DES_LIEUX.md` est trop optimiste.** Il indique des modules « ✅ Fonctionnel » (Espaces CRUD, Capteurs, Notifications, Catalogue) qui sont en réalité cassés ou partiellement cassés.

**Dette estimée pour atteindre la v1.0 : environ 30 j/h.** Ce plan la répartit sur 8 semaines.

---

## 2. Observations détaillées

### 2.1 Dépôt git et hygiène (🔴)

| Constat | Impact |
|---|---|
| `back_end/.env` est **suivi** par git (le `.gitignore` ne retire pas un fichier déjà suivi) | Un simple `git add .` publierait la nouvelle `SECRET_KEY` |
| `back_end/green_guard.db` est versionné : 2 admins, 200 espaces, 1 839 plantes | Fuite de données personnelles et de hash ; risque de backdoor |
| Clé OpenWeather et secret JWT présents dans l'historique **et** dans `HEAD` | Il faut faire tourner les clés, puis purger l'historique |
| `front_end/node_modules` est commité (**10 119 fichiers**), ainsi que `.vite/`, `dist/` et 61 `__pycache__` | Dépôt lourd, diffs illisibles, lint pollué (294 erreurs viennent de `.vite/`) |
| `inaturalist` est un sous-module git **cassé** (gitlink sans `.gitmodules`) | Un `clone` récupère un dossier vide |
| `hygiene_et_securite.yml` est à la racine, pas dans `.github/workflows/`, et ne fait qu'un `echo` | **Aucune CI n'a jamais tourné** |
| 6 branches distantes abandonnées (`master`, `front-kourosh`, `feature/Lucresse-branche` avec 5 commits non fusionnés, etc.) | Confusion ; travail potentiellement perdu (CRUD interventions) |
| Remote parasite `or` → URL `.../tree/master` invalide | Bruit |
| README : « en cas de conflit, priorité absolue à la version locale » | Règle dangereuse qui a déjà écrasé du travail (commits `0096ddb`, `bec2505`) |
| 26 fichiers modifiés non commités, issus de la session précédente | Travail utile mais non revu, non publié |

### 2.2 Back-end (FastAPI)

**🔴 Bloquants vérifiés à l'exécution**
- **Préfixes doublés** : 7 routers déclarent leur `prefix`, et `main.py:36-47` en ajoute un second. Le `tokenUrl` OAuth2 pointe donc vers une route inexistante, et le bouton Authorize de Swagger est cassé.
- **`ImportError`** : `PlanteEntity` est importé par 8 modules alors qu'il n'existe pas, et `from schema import DonneesMeteoJournalieres` n'existe pas non plus. Tout le flux « bilans hydriques journaliers » et « compatibilité plante » est donc mort.
- **Erreurs 500** sur :
  - `POST /espaces-verts/` : le schéma contient des champs absents du modèle ;
  - `GET /users/me/notifications` et `GET /notifications/` : écart de noms `is_read`/`est_lue` ;
  - `/interventions/urgent` : le repository est instancié sans `db` ;
  - `POST /plants/` ;
  - `/vegetal/*` : appelle `list_tous`, qui n'existe pas ;
  - `POST /zones/clustering/rebuild` et `GET /zones/zones` dès qu'une zone existe.
- **Ports et implémentations désynchronisés** : les use cases appellent `list_tous`, `get_par_id`, `sauvegarder`… alors que les implémentations exposent `get_by_id`, `save`… Le filtre utilise `date_bilan` alors que la colonne s'appelle `date`.
- **Job planifié** (`capteur_hybrid_service.py`) : il écrit `reserve_eau`, une colonne qui n'existe pas. L'exception est avalée par un `print`. Toutes les 2 minutes, il retire l'ET0 *journalière* : la réserve se viderait 720 fois par jour. Il est lancé dans **chaque** worker uvicorn.
- **Dépendance cachée** : `python_weather` est importé sans être utilisé ni déclaré, et `pandas` manque aussi. Une installation propre, et donc l'image Docker, plante au démarrage.
- **Scripts cassés** : `init_db.py`, `sanity_check.py` et `test_weather.py`. Ce dernier lance un appel réseau à l'import, ce qui casse `pytest`.

**🟠 Sécurité**
- **IDOR** :
  - `GET /plants/` renvoie les espaces de **tous** les utilisateurs ;
  - `GET /capteurs/dashboard` accepte n'importe quels `espace_ids` (défaut `[1,2,3,4]`) ;
  - `/health/diagnostic` ne vérifie pas le propriétaire et renvoie des valeurs **aléatoires**.
- **Routes sans authentification** : `/catalogue/*` (ORM brut, sans pagination) et `/meteo/*` (proxy ouvert).
- **Login et inscription** :
  - pas de limitation de débit ;
  - mot de passe `"1"` accepté ;
  - `is_active` n'est pas vérifié au login ni dans `get_current_user`.
- **JWT et dépendances** : `python-jose` est peu maintenu (CVE `ecdsa`) et doit être remplacé par **PyJWT**. `utcnow()` est déprécié. Il n'y a ni `iat`, ni `jti`, ni refresh token.
- **Robustesse** :
  - le message d'exception est renvoyé au client (`meteo.py:33`) ;
  - `OpenMeteoService` renvoie `None`, ce qui provoque ensuite un `AttributeError` en cascade ;
  - aucun header de sécurité.
- **Docker** : le healthcheck appelle `/ping`, qui n'existe pas, et `--reload` est activé en production.

**🟠 Architecture**
- **Le domaine dépend de l'infrastructure** : `domain/models.py` hérite du `Base` SQLAlchemy, et `domain/logic/clustering.py` reçoit une `Session` et fait des `commit`.
- **Doublons** :
  - 2 ports `IEspaceVertRepository` ;
  - 2 `IMeteoService` ;
  - 3 versions de la « compatibilité plante » ;
  - 2 algorithmes de zones ;
  - 2 endpoints health ;
  - un 2e `register` mort dans `api/deps/auth.py` ;
  - `schema/utilisateurs.py` fourre-tout, en doublon de `schema/token.py`, `schema/espaces_verts.py` et `schema/zones.py` ;
  - l'endpoint `plants` gère en réalité des espaces verts.
- **12 fichiers vides**.

**🟠 Base de données**
- **Contraintes manquantes** :
  - presque tout est nullable, y compris `users.email`, `hashed_password` et `espaces_verts.user_id` ;
  - aucun `ondelete` ;
  - aucun index sur les FK ni sur `mesures(espace_id, timestamp)` ;
  - pas d'unicité sur `bilans(espace_id, date)`.
- **Bug de date** : `BilanHydriqueJournalier.date` a pour défaut `datetime.utcnow().date()`, **évalué une seule fois à l'import**.
- **Types** : dates naïves (sans fuseau horaire) ; rôles et statuts en `String` libre.
- **Double création du schéma** : la migration Alembic `ab36bd25cc59` existe, mais `main.py` fait aussi `Base.metadata.create_all`. C'est une double source de vérité du schéma.

**🟡 Logique métier**
- **Clustering** : c'est un KMeans et non un DBSCAN comme documenté. Les centroïdes sont enregistrés dans l'espace *standardisé*, donc ce ne sont pas des lat/lon réelles.
- **Tri des interventions inversé** : le tri alphabétique place `low` avant `critical`.
- **Alertes et indicateurs faux** : l'alerte « Sec » est toujours déclenchée (valeur par défaut 12,5 < seuil 15), et une moyenne en mm est affichée comme un pourcentage.
- **Libellés incohérents** : « Confort » d'un côté, « Optimal » de l'autre.
- **`sante.py`** : inutilisable, il dépend de champs inexistants.
- **Valeurs non documentées** : plus de 50 constantes magiques non sourcées (voir HR-1), et « 2025 » écrit en dur dans les projections carbone.

**Tests** : **0 test réel.** `pytest` s'arrête sur une erreur de collecte.

### 2.3 Front-end (React 19 / Vite / Tailwind 4)

**🔴 Bloquants**
- **Fonctions absentes de `api.js`** : `api.createEspace`, `api.updateEspace`, `api.triggerAction` et `api.getEspaceVertById` n'existent pas. Conséquences : création et édition d'espace impossibles, boutons d'action du dashboard inopérants, fil d'Ariane cassé.
- **KPI du dashboard toujours vides** : le DTO backend ne contient ni `sante_percent`, ni `nom`, ni `statut`. La matrice d'intervention ne s'affiche jamais.
- **Contrat d'URL** : la météo renvoie un 404. Les autres appels contournent le préfixe doublé avec des URLs `/auth/auth/...`, qui casseront dès que le backend sera corrigé : il faut corriger les deux en même temps.
- **`/parametres`** renvoie vers le login, car la route est absente et le catch-all redirige vers `/login`. Il n'y a pas de page 404.
- **Docker** : `front_end/Dockerfile` est absent alors que `docker-compose.yml` le référence, donc `docker compose up --build` échoue. De plus, `VITE_API_URL` passé au runtime n'a aucun effet, car la variable est lue au build.

**🟠 Important**
- **Authentification** :
  - deux `AuthProvider` imbriqués ;
  - `isAuthenticated = !!token`, sans vérifier l'expiration ;
  - aucun traitement global des 401 ;
  - token en `localStorage`.
- **Données factices présentées comme réelles** : « Lyon : 24 °C », notifications en dur, rapports en dur avec un bouton Télécharger qui ne fait rien, « Admin Principal ».
- **Environ 20 fichiers morts ou dupliqués** : `Header.jsx` (imports cassés, dépendances non installées), deux `AlertsPanel`, deux `AddSpaceModal`, `types/domain.ts` désaligné, `src/data/*.js` vides, `NotificationCenter` rangé dans `assets/`.
- **Filtre par cluster cassé** : `zone_id` est absent du DTO. Le modal d'édition enverra `""`, ce qui déclenchera des 422.

**🟡 Design, UX, accessibilité**
- **Pas de design system effectif** :
  - `tailwind.config.js` est au format v3 et ignoré par Tailwind v4 ;
  - les animations `animate-in` n'ont aucun effet ;
  - couleurs hexadécimales en dur ;
  - `slate` et `gray` mélangés ;
  - mode sombre forcé, `ThemeProvider` jamais monté.
- **Accessibilité** :
  - inputs sans `<label>` ;
  - boutons-icônes sans `aria-label` ;
  - `div onClick` à la place de boutons ;
  - textes de 8 à 10 px ;
  - `outline-none` sans focus visible.
- **Identité incohérente** : « Green_Tech », « GreenTech » et « Green Guard » ; `lang="en"` ; favicon Vite ; package `jeu_entreprise` ; jargon anglais (`Sync_Bio_Kernel`, `Fleet_Integrity`).
- **Lint et outillage** : 24 erreurs de lint dans `src/`. `rolldown-vite` est expérimental. TypeScript est configuré mais inutilisé. Il n'y a ni tests ni Prettier.

---

## 3. Décisions d'architecture proposées (ADR courts)

| # | Décision | Justification |
|---|---|---|
| ADR-1 | **Un seul préfixe**, porté par `main.py`. Les `APIRouter` n'ont pas de `prefix`. | Supprime toute une famille de bugs ; contrat lisible |
| ADR-2 | **Contrat API unique** : le front consomme un client généré à partir de `openapi.json` (ou au minimum un `request()` centralisé), et la CI vérifie la cohérence. | 80 % des bugs constatés sont des écarts de contrat |
| ADR-3 | **Domaine pur** : entités en dataclasses dans `domain/`, modèles ORM déplacés dans `infrastructure/persistence/models.py`, mapping dans les repositories. Une seule version de chaque port. | Rend l'architecture Onion réelle et la logique testable sans BDD |
| ADR-4 | **Alembic est la seule source du schéma** : suppression de `create_all`, nouvelle migration avec contraintes, index et `TIMESTAMPTZ`. | Reproductibilité, intégrité |
| ADR-5 | **Jobs hors du process API** : le scheduler devient un service `worker` dédié dans docker-compose. Le bilan hydrique est calculé **une fois par jour et par espace**, de façon idempotente (contrainte d'unicité). | Corrige la vidange ×720 et l'exécution multi-workers |
| ADR-6 | **PyJWT** à la place de python-jose, **cookie httpOnly + SameSite=Lax** à la place du `localStorage`, rate limiting avec `slowapi`, politique de mot de passe (12 caractères minimum). | Sécurité standard pour une v1 publique |
| ADR-7 | **Front** : suppression du code mort, TanStack Query pour les données serveur, tokens de design en `@theme` Tailwind 4, retour à `vite` stable. Migration TypeScript progressive après la v1. | Fiabilité et cohérence visuelle |
| ADR-8 | **Configuration centralisée** avec `pydantic-settings` : seuils agronomiques et paramètres dans un module documenté et sourcé. | Corrige les constantes magiques ; prépare HR-1 |

---

## 4. Plan d'action et calendrier

Hypothèse : un développeur à temps plein accompagné de l'architecte. Chaque phase se termine par un tag et une mise à jour de ce document.

### Phase 0 : mise en sécurité (5 → 9 octobre)
1. **Rotation** de la clé OpenWeather (elle n'est plus utilisée : la révoquer) et génération d'une nouvelle `SECRET_KEY`. **Changement des mots de passe des 2 comptes admin** présents dans la BDD publiée.
2. `git rm --cached` sur `back_end/.env`, `green_guard.db`, `front_end/node_modules`, `.vite`, `dist` et `__pycache__`. Écriture d'un `.gitignore` complet et d'un `.env.example`.
3. Relecture puis **commit du travail en attente** de juin (26 fichiers) en commits atomiques.
4. **Purge de l'historique** avec `git filter-repo` (secrets, `.db`, `node_modules`), puis push forcé coordonné avec l'équipe. *Cette étape demande ton accord explicite.*
5. Réparation ou suppression du sous-module `inaturalist`. Suppression des branches mortes, après avoir récupéré le CRUD interventions de `feature/Lucresse-branche` si on le garde.
6. Activation de la protection de `main` sur GitHub et du *secret scanning / push protection*. Suppression de la règle « priorité au local » du README.

**Suivi au 2026-10-03** (branche `chore/phase-0-securisation`, 6 commits) :
- ✅ Étape 2 : secrets, BDD, `node_modules`, `.vite`, `dist` et `__pycache__` retirés de l'index ; `.gitignore`, `.dockerignore` et `.env.example` en place ; `SECRET_KEY` locale régénérée.
- ✅ Étape 3 : travail de juin relu et commité en 3 commits (sécurité back, sécurité front, PostgreSQL/Alembic, migration vérifiée avec `alembic check`).
- ✅ Étape 5 (partielle) : gitlink `inaturalist` retiré. La branche `feature/Lucresse-branche` (CRUD interventions, historique séparé) est **à conserver** jusqu'à son report en phase 1.
- ✅ CI : scan de secrets réel (`.github/workflows/securite.yml`). README corrigé.
- ⏳ Étapes 1, 4 et 6, ainsi que la suppression des branches mortes : en attente du porteur de projet (rotation des clés, accord pour la purge, réglages GitHub).

### Phase 1 : faire marcher le produit (12 → 23 octobre)
1. ADR-1 (préfixes) et alignement du front.
2. Correction des 10 routes en 500 et des `ImportError` : décider pour chaque module mort entre **réparer** et **supprimer**.
3. Ports et repositories : une seule interface par agrégat, noms alignés.
4. Migration Alembic n°2 : NOT NULL, FK `ondelete`, index, unicités, `TIMESTAMPTZ`, correction du défaut de date. Suppression de `create_all`.
5. Front : `createEspace`, `updateEspace`, `getEspaceVertById`, route `/parametres`, page 404, un seul `AuthProvider`, traitement global des 401. Décision sur `triggerAction` : endpoint « déclencher une intervention » ou retrait des boutons.
6. Suppression du code mort (back : 12 fichiers vides et doublons ; front : environ 20 fichiers).
7. `requirements.txt` épuré et figé avec `uv` ou `pip-tools`. Correction du `Dockerfile` back et création du `Dockerfile` front (multi-stage + nginx).

**Critère de sortie** : un parcours complet fonctionne sous Docker (inscription → connexion → créer un espace → dashboard réel → météo → déconnexion).

**Suivi au 2026-10-03** (branche `fix/phase-1-fonctionnel`, 5 commits, au-dessus de la phase 0) : **critère de sortie atteint**, parcours validé dans un navigateur sur la pile Docker avec la météo réelle.
- ✅ Étapes 1 à 5 et 7. Routes : 33 routes, préfixe unique, plus aucune erreur 500 sur le parcours. Schéma v1 avec contraintes. Front branché. Dockerfiles front et back. Dépendances figées.
- ✅ Bonus phase 2 réalisé en avance :
  - 22 tests verts, sur SQLite et sur PostgreSQL 16 ;
  - IDOR corrigés (dashboard, plants, diagnostic) ;
  - catalogue et météo authentifiés ;
  - comptes désactivés bloqués ;
  - mot de passe de 12 caractères minimum ;
  - job idempotent ;
  - clustering corrigé.
- ⚠️ Migration de référence remplacée par `0001_schema_v1` : une base de développement créée en juin doit être recréée.
- ⏳ Étape 6 (suppression du code mort) : refusée par le garde-fou automatique, **en attente de l'accord du porteur de projet**. Ces fichiers ne sont ni importés par l'API ni inclus dans le bundle front.
  - Back (environ 40 fichiers) : catalogue v2 `PlanteEntity`, ports dupliqués, repositories vides, `plants.py`, `init_db.py`, `sanity_check.py`, `test_weather.py`, `run.sh`.
  - Front (environ 20 fichiers) : `Header.jsx`, `navbar/*`, doublons `AddSpaceModal`/`AlertsPanel`, `src/data/*`, `types/domain.ts`, `NotificationCenter.jsx`.
- Reporté en phase 3 : page Rapports (données factices), labels de formulaires non associés, wording restant.

### Phase 2 : fiabilité et sécurité (26 octobre → 6 novembre)
1. **Tests** :
   - pytest avec `conftest.py` (BDD de test, override de `get_db`) ;
   - tests unitaires de `domain/logic` (bilan, stress, clustering, interventions) ;
   - tests d'API sur toutes les routes, y compris l'**isolation entre utilisateurs** (IDOR).
   - Objectif : 70 % de couverture sur domaine et application.
2. Sécurité :
   - correction des IDOR : `plants`, `capteurs/dashboard`, `diagnostic` ;
   - authentification sur catalogue et météo, pagination ;
   - PyJWT, cookie httpOnly, `slowapi`, politique de mot de passe, contrôle de `is_active` ;
   - headers de sécurité, erreurs génériques.
3. ADR-5 : service worker, bilan journalier idempotent, logs structurés, plus aucun `print`.
4. Logique métier : clustering avec de vrais centroïdes (géodésique ou DBSCAN haversine en km), tri des priorités, statuts unifiés, alertes persistées, KPI santé recalculés.
5. **CI GitHub Actions** (`.github/workflows/ci.yml`) :
   - lint (ruff, eslint), tests, build front ;
   - `pip-audit` et `npm audit` ;
   - gitleaks ;
   - vérification « migration Alembic à jour ».

**Suivi au 2026-10-04** (branche `feat/phase-2-fiabilite`, au-dessus des phases 0 et 1) : **phase 2 terminée**, avec un mois d'avance sur le calendrier.
- ✅ **Tests** : 69 tests, **96 % de couverture** sur le domaine, l'application, l'API et l'infrastructure (objectif : 70 %). Suite verte sur SQLite et PostgreSQL 16.
- ✅ **Sécurité** :
  - PyJWT ;
  - session par cookie httpOnly avec protection CSRF ;
  - limitation de débit sur la connexion et l'inscription ;
  - en-têtes de sécurité et CSP sur l'API et le front ;
  - erreurs 500 génériques ;
  - `SECRET_KEY` de 32 caractères minimum ;
  - 4 CVE Python et 5 vulnérabilités npm hautes corrigées (pip-audit et npm audit à zéro).
- ✅ **ADR-5** : service worker dédié, logs JSON, plus de `print` dans l'application.
- ✅ **Métier** :
  - alertes de stress critique persistées sous forme de notifications ;
  - lectures capteurs sans N+1 ;
  - facteur de sol branché sur les types saisis dans l'interface.
- ✅ **CI** (`ci.yml`) : ruff, pytest avec seuil de couverture, migrations et tests sur PostgreSQL, audits, build des images. Lint front à 0 erreur.
- ✅ **ADR-8** : configuration centralisée (`config.py`).
- ⚠️ Développement local sans worker : ajouter `ENABLE_SCHEDULER=true` dans `back_end/.env` (voir `.env.example`).
- ⏳ La CI ne tournera qu'après le push (point 2 de la phase 0, toujours en attente).

### Phase 3 : qualité produit (9 → 20 novembre)
1. **Design system** : tokens `@theme` (couleurs, typo, espacements, rayons), clair et sombre via `ThemeProvider`, composants de base (Button, Input avec label, Card, Modal, Badge, Toast).
2. **Accessibilité** WCAG 2.1 AA : labels, `aria-*`, focus visible, taille de texte minimale 12 px, navigation clavier, contrastes.
3. **Identité et contenu** : un seul nom de marque (« GreenGuard »), `lang="fr"`, favicon, wording 100 % français et métier, suppression de toutes les données factices (remplacées par des états vides honnêtes).
4. **Rapports** : export réel CSV/PDF, ou retrait de la page de la v1.
5. **Données front** : TanStack Query, états de chargement et d'erreur, polling suspendu quand l'onglet est masqué.
6. **Observabilité** : `/health` (liveness) et `/ready` (BDD), logs JSON, Sentry en option.
7. Documentation : README d'installation fiable, `Doc_back_end.md` à jour, contrat OpenAPI publié.

**Suivi au 2026-10-04** (branche `feat/phase-3-qualite`) : **phase 3 terminée**, avec six semaines d'avance.
- ✅ **Design system** : tokens sémantiques (Tailwind 4 `@theme`), thèmes clair, sombre et système, composants Button, Field, Modal, Card, Badge, Alert et Logo. Toutes les couleurs brutes ont été migrées. Guide : `documentation/design_system.md`.
- ✅ **Accessibilité WCAG AA** :
  - contrastes calculés (texte ≥ 4,5:1 dans les deux thèmes) ;
  - libellés reliés à leurs champs, focus visible, lien d'évitement, repères `nav`/`main`, `aria-current` ;
  - modales accessibles, texte de 12 px minimum, `prefers-reduced-motion` respecté, titre par page.
  - Vérifié au clavier et au lecteur d'accessibilité dans le navigateur.
- ✅ **Identité** : marque unique « GreenGuard », `lang="fr"`, favicon, textes en français, plus aucun jargon anglais ni donnée factice.
- ✅ **Rapports** (D-6, version minimale) : historique réel des interventions, filtres, export CSV, impression. **Paramètres** réels. Catalogue paginé.
- ✅ **Données front** : hook `useRequete` (chargement annulable) au lieu de TanStack Query. Le volume actuel ne justifie pas une dépendance de plus ; à réévaluer après la v1.
- ✅ **Observabilité** : sondes `/health/live` et `/health/ready`, logs JSON (phase 2). Sentry reporté (optionnel).
- ✅ **Documentation** : `Doc_back_end.md` et `Documentation_Usecases.md` réécrits ; contrat d'API publié par OpenAPI (`/docs`).
- ⏳ À valider par le porteur de projet : la version minimale des Rapports (D-6) et les seuils agronomiques (D-4).

**20 novembre : gel des fonctionnalités.**

### Phase 4 : release candidate et recette (23 → 27 novembre)
- Tag `v1.0.0-rc1`. Recette fonctionnelle complète, tests de charge légers (200 espaces), revue de sécurité finale, sauvegarde/restauration PostgreSQL testée.
- Seuls les correctifs bloquants sont acceptés.

**Suivi au 2026-10-04** (branche `release/v1.0.0-rc1`, tag local `v1.0.0-rc1`) : **phase 4 terminée**. Rapport : `documentation/recette_v1.0.0-rc1.md`.
- ✅ Tests de bout en bout Playwright (bureau et mobile) et audit axe-core WCAG AA : 20/20, 0 violation sérieuse.
- ✅ Test de charge sur 200 espaces. Il a révélé un **interblocage critique de l'API**, corrigé, ainsi que des N+1 (`/espaces-verts/` est passé de 3,3 s à 0,3 s).
- ✅ Sauvegarde et restauration testées ; revue de sécurité ; audits à zéro ; version, CHANGELOG, guide d'exploitation.
- ⚠️ Réserve n° 1 : le p95 du tableau de bord (540-660 ms, pour un objectif de 500) est à re-mesurer sur l'hébergement cible (D-7).
- ⚠️ Réserve n° 2 : rotation des clés, purge de l'historique et réglages GitHub, à faire avant la mise en ligne.
- Calendrier : la recette prévue du 23 au 27 novembre est réalisée. Il reste avant le 1er décembre : lever les réserves, valider D-4, D-6 et D-7, puis faire une recette métier par les utilisateurs.

### 🚀 v1.0.0 : mardi 1er décembre 2026

---

## 5. Points qui demandent une décision du porteur de projet

| # | Question | Pourquoi c'est bloquant |
|---|---|---|
| D-1 | **M'autorises-tu la purge de l'historique git et le push forcé** ? | Réécrit l'historique ; les autres contributeurs devront re-cloner |
| D-2 | Qui a accès au compte OpenWeather et aux 2 comptes admin, pour la rotation ? | Je ne peux pas le faire moi-même |
| D-3 | Capteurs : simulation définitive pour la v1, ou intégration IoT réelle ? (HR-3) | Change le périmètre de la phase 2 |
| D-4 | Seuils agronomiques : qui les valide ? (HR-1) | La v1 affichera des recommandations d'arrosage |
| D-5 | `inaturalist` (classification) : hors v1 ? | Je propose de le sortir du dépôt |
| D-6 | Page Rapports et boutons d'action du dashboard : à implémenter ou à retirer de la v1 ? | Impact sur le planning de la phase 3 |
| D-7 | Cible d'hébergement de la production (VPS + Docker, Render, Scaleway…) ? | Conditionne la phase 3 (TLS, domaine, sauvegardes) |

---

## 6. Améliorations post-v1 (backlog)
- Migration TypeScript du front, client API généré.
- Cartographie réelle des espaces (MapLibre) avec les zones intelligentes.
- Notifications temps réel (SSE ou WebSocket) et e-mail.
- Multi-tenant (collectivités) et rôles fins (admin / gestionnaire / technicien).
- Module de reconnaissance de plantes (dataset iNaturalist).
- Historique et graphiques (bilans hydriques, carbone) avec export.

---

*Ce document remplace `documentation/archives/ETAT_DES_LIEUX.md` comme référence. Il sera mis à jour à la fin de chaque phase.*
