# Documentation technique du back-end GreenGuard

> À jour au 2026-10-04 (phase 3, multi-organisations). Le **contrat d'API de référence** est le schéma OpenAPI
> généré par FastAPI : `http://localhost:8000/docs` (Swagger) ou `/openapi.json`, servis
> uniquement si `ENABLE_DOCS=true` (développement ; 404 sinon).

## 1. Architecture

Architecture en couches (Onion) : les dépendances vont toujours vers le domaine.

| Couche | Dossier | Rôle |
|---|---|---|
| Domaine | `domain/logic/`, `domain/ports/`, `domain/models.py` | Calculs purs (bilan hydrique, stress, clustering, arrosage, carbone, droits par rôle, slugs d'organisation) et interfaces (ports) |
| Application | `application/use_cases/`, `application/dto/` | Orchestration des cas d'usage, objets de sortie |
| Infrastructure | `infrastructure/` | Base de données, repositories, services externes (Open-Meteo), job planifié, logs |
| API | `api/`, `schema/`, `main.py` | Routes FastAPI, authentification, middlewares, schémas de validation |

Écart connu (ADR-3, post-v1) : les entités du domaine sont encore des modèles SQLAlchemy
(`domain/models.py`). La logique de `domain/logic/` n'accède jamais à la base, ce qui la
rend testable sans base (voir `tests/test_domaine.py`).

```text
back_end/
├── main.py                      # Application FastAPI : middlewares, CORS, routes (préfixe unique /api/v1)
├── worker.py                    # Service worker : tâches planifiées (une seule instance)
├── config.py                    # Seul module qui lit les variables d'environnement
├── api/
│   ├── deps/auth.py             # bcrypt, JWT (PyJWT), cookie de session, CSRF, exiger_role / exiger_superadmin
│   ├── deps/rate_limit.py       # Limitation de débit (login, inscription)
│   ├── middleware.py            # En-têtes de sécurité, X-Request-ID, journal d'accès, erreur 500 générique
│   └── v1/endpoints/            # Une ressource par fichier
├── application/use_cases/       # capteurs, interventions, zones, météo, végétal, bilans journaliers, organisations
├── domain/logic/                # stress_hydrique, bilan_hydrique, stress_sanitaire, arrosage, bilan_carbone, clustering,
│                                # droits (rôles → permissions), organisations (slug, nom par défaut)
├── infrastructure/
│   ├── database.py              # Moteur SQLAlchemy, convention de nommage des contraintes
│   ├── rls.py                   # Contexte d'organisation des transactions PostgreSQL (Row Level Security)
│   ├── jobs/mise_a_jour_capteurs.py
│   ├── repositories/            # espaces verts, bilans hydriques, organisations et membres
│   └── services/                # Open-Meteo (avec cache), lecture capteurs groupée
├── alembic/                     # Migrations : seule source du schéma
├── scripts/load/taxonomy.py     # Chargement du catalogue iNaturalist
└── tests/                       # pytest (SQLite par défaut, PostgreSQL via TEST_DATABASE_URL)
```

## 2. Ressources de l'API (`/api/v1`)

Une instance sert plusieurs **organisations** (collectivités) totalement cloisonnées ; les membres
d'une même organisation partagent son patrimoine. Lecture : tout membre. Écriture : selon le rôle (§ 3).

| Préfixe | Lecture | Écriture | Contenu |
|---|---|---|---|
| `/auth` | public (limité en débit) | public | `POST /login` (formulaire OAuth2), `POST /register` (JSON, crée une organisation), `POST /logout` |
| `/users` | connecté | — | `GET /me` (dont `organisation {id, nom}`, `role`, `permissions`, `est_superadmin`), `GET /me/notifications` |
| `/organisations` | connecté | voir colonne Contenu | `GET /moi` ; `PUT /moi` (paramètres : gestionnaire ; nom : admin) ; `GET /moi/membres` ; `PUT /moi/membres/{id}` (admin : rôle, désactivation) ; `POST /` (superadmin : organisation + premier admin) |
| `/espaces-verts` | connecté | gestionnaire | CRUD complet |
| `/zones` | connecté | gestionnaire | `GET /`, `POST /clustering/rebuild` |
| `/capteurs` | connecté | — | `GET /dashboard` (synthèse, lectures, météo extérieure) |
| `/interventions` | connecté | technicien (création, suivi) ; gestionnaire (suppression) | `GET /urgent`, CRUD |
| `/notifications` | connecté (les siennes) | connecté (les siennes) | liste, `POST /{id}/mark-as-read` |
| `/catalogue` | connecté | — | `GET /plantes`, `GET /auxiliaires` (pagination `offset`/`limit`) |
| `/meteo` | connecté | — | `GET /actuelle?lat&lon`, `GET /{ville}` |
| `/vegetal` | gestionnaire | — | `GET /etat-global`, `GET /impact-carbone` (patrimoine de l'organisation) |
| `/health` | public / connecté | — | `GET /live`, `GET /ready` (base), `POST /diagnostic` (lecture seule) |

« gestionnaire » se lit « gestionnaire ou admin », « technicien » « technicien, gestionnaire ou admin ».

Règle d'isolation : toute ressource est filtrée sur l'**organisation** de l'utilisateur (directement,
ou via l'espace auquel elle est rattachée) ; les notifications restent personnelles. Un objet d'une
autre organisation répond **404** (et non 403), pour ne pas révéler son existence.

**Inscription (provisoire)** : `POST /auth/register` crée une nouvelle organisation (`organisation`,
facultatif, sinon « Organisation de <nom> ») dont le compte est administrateur. Rejoindre une
organisation existante passera par une invitation (lot Confiance) ; d'ici là, l'admin de la plateforme
ajoute les agents avec `create_user.py --organisation <slug> --role <rôle>`.

## 3. Sécurité

- **Session** : JWT HS256 (60 min, `iat`, `jti`, `type`) dans le cookie `gg_session`
  (`HttpOnly`, `Secure`, `SameSite=Lax`, chemin `/api`). L'en-tête `Authorization: Bearer`
  reste accepté pour Swagger et les scripts.
- **CSRF** : une écriture authentifiée par cookie exige l'en-tête `X-Requested-With`.
- **Mots de passe** : bcrypt, 12 caractères minimum. **`SECRET_KEY`** : 32 caractères minimum.
- **Rôles** dans l'organisation, relus en base à chaque requête (jamais depuis le jeton) ; un compte
  désactivé perd l'accès immédiatement. Dépendance `exiger_role(*roles)` sur toutes les routes d'écriture
  (`domain/logic/droits.py`) :

  | Rôle | Droits |
  |---|---|
  | `lecteur` (élu) | consultation seule |
  | `technicien` | + créer et suivre (terminer) une intervention |
  | `gestionnaire` | + espaces, zones, suppression d'intervention, paramètres métier, indicateurs végétaux |
  | `admin` | + nom de l'organisation, membres (rôle, désactivation) ; l'organisation garde toujours un admin actif |

  `est_superadmin` (administrateur de la plateforme, indépendant du rôle) : création d'organisations.
- **Isolation par la base** (défense en profondeur, PostgreSQL) : Row Level Security avec
  `FORCE ROW LEVEL SECURITY` (migration `0002_organisations`). Politique :
  `organisation_id = app.organisation_id OR app.contourner_rls = 'on'` sur `organisations`, `users`,
  `espaces_verts`, `zones_intelligentes`, `clustering_configs` (la configuration d'instance, sans
  organisation, reste lisible par tous) ; sous-requête sur `espaces_verts` pour les tables rattachées
  à un espace (mesures, bilans, capteurs, interventions, alertes, arrosages, zone_espaces) ; sur `users`
  pour les notifications. Le contexte est posé en local à la transaction (`set_config(…, true)`, comme
  `SET LOCAL`) et donc **reposé au début de chaque transaction** par l'événement `after_begin` de la
  fabrique de sessions, à partir de `session.info` renseigné par l'authentification (`infrastructure/rls.py`).
  Contournement explicite et limité : lecture du compte à l'authentification, inscription, création
  d'organisation, liste des organisations par le worker (chaque organisation est ensuite traitée dans
  son contexte), scripts d'administration, migrations Alembic. **La RLS ne s'applique pas à un
  superutilisateur ni à un rôle `BYPASSRLS`** : l'API doit se connecter avec un rôle dédié
  (voir `exploitation.md`) ; sinon elle l'indique au démarrage par un avertissement. Sous SQLite, seul le
  filtrage applicatif s'applique.
- **Limitation de débit** (en mémoire, fenêtre `AUTH_RATE_WINDOW_S`) : la connexion est limitée
  par identifiant (e-mail en minuscules, `AUTH_RATE_LIMIT`) **et** par IP (`AUTH_RATE_LIMIT_IP`, large :
  toute une collectivité peut sortir par la même IP) ; l'inscription par IP (`AUTH_RATE_LIMIT`).
  Le 429 est identique que le compte existe ou non. Derrière un reverse proxy, l'IP du client n'est
  connue que si ce proxy figure dans `TRUSTED_PROXIES` (`--forwarded-allow-ips` d'uvicorn).
- **Documentation interactive** (`/docs`, `/redoc`, `/openapi.json`) : fermée par défaut (`ENABLE_DOCS`).
- **En-têtes** : CSP stricte (sauf `/docs` quand elle est ouverte), `X-Frame-Options: DENY`, `nosniff`,
  `Referrer-Policy`, HSTS si `HSTS=true`. Les erreurs 500 ne renvoient qu'un message
  générique et un `request_id` à retrouver dans les logs.

## 4. Métier

### Bilan hydrique journalier
`application/use_cases/generer_bilans_hydriques_journaliers.py`, appelé chaque heure par le worker.

Le « jour » est celui de `FUSEAU_HORAIRE` (Europe/Paris par défaut), pour le bilan comme pour les
cumuls météo demandés à Open-Meteo : un passage à 0 h 30 (heure de Paris) produit le bilan du jour
qui commence sans écraser celui de la veille. Arrosages et notifications sont comptés sur ce même jour.

1. Météo du jour (Open-Meteo) : ET0 et cumul de pluie, mis en cache par point (~10 km, 15 min).
2. Point de départ : dernier bilan **antérieur** au jour (réserve pleine s'il n'y en a pas).
3. `réserve = réserve_veille + pluie + arrosage − ET0 × Kc × facteur_sol`, bornée à [0, RU max].
4. `indice de stress = 1 − réserve / RU max` → *Optimal* (< 0,3), *A surveiller* (< 0,6), *Critique*.
5. Le bilan du jour est **remplacé** s'il existe déjà (idempotent : relancer ne décompte pas deux fois).
6. Une mesure est enregistrée ; un espace *Critique* déclenche une notification (une par jour).

Les seuils (0,3 / 0,6) et les facteurs de sol restent **à faire valider par un agronome** (décision D-4).

### Impact carbone (estimation grossière)
`domain/logic/bilan_carbone.py` : séquestration des arbres urbains selon Nowak & Crane (2002),
0,306 kg C par m² de couvert arboré et par an, soit ≈ 1,12 kg CO₂/m²/an (× 44/12), appliquée comme
**majorant** (surface supposée entièrement arborée), réduite par le stress du jour puis projetée sur
l'année (× 365). `GET /vegetal/impact-carbone` renvoie `estimation_grossiere: true` et `methode`
(texte court à afficher avec le chiffre) ; totaux et détail par zone portent sur la même période.

### Zones intelligentes
`domain/logic/clustering.py` : K-Means sur les coordonnées projetées en km. Nombre de zones
dans `clustering_configs.n_clusters` (configuration de l'organisation, sinon celle de l'instance,
sinon 5). Les zones appartiennent à l'organisation : un recalcul remplace celles de toute l'organisation. Les centroïdes et rayons sont en coordonnées réelles.

## 5. Configuration (variables d'environnement)

| Variable | Défaut | Rôle |
|---|---|---|
| `DATABASE_URL` | — (obligatoire) | Connexion PostgreSQL |
| `SECRET_KEY` | — (obligatoire, ≥ 32) | Signature des JWT |
| `FRONTEND_URL` | — | Origine CORS supplémentaire |
| `COOKIE_SECURE` | `true` | Cookie de session réservé à HTTPS (localhost accepté) |
| `ACCESS_TOKEN_MINUTES` | `60` | Durée de session |
| `AUTH_RATE_LIMIT` / `AUTH_RATE_WINDOW_S` | `10` / `60` | Connexion : tentatives par identifiant ; inscription : par IP (par fenêtre, en s) |
| `AUTH_RATE_LIMIT_IP` | `100` | Connexion : tentatives par IP et par fenêtre |
| `TRUSTED_PROXIES` | `127.0.0.1` | Proxys (adresses ou CIDR) dont `X-Forwarded-For` est cru (CMD du Dockerfile) |
| `ENABLE_DOCS` | `false` | Ouvre `/docs`, `/redoc`, `/openapi.json` (développement) |
| `FUSEAU_HORAIRE` | `Europe/Paris` | Jour métier du bilan et des cumuls météo (nom IANA) |
| `ENABLE_SCHEDULER` | `false` | Job intégré à l'API (développement sans worker) |
| `LOG_FORMAT` / `LOG_LEVEL` | `text` / `INFO` | `json` en production |
| `HSTS` | `false` | À activer derrière HTTPS |

## 6. Exploitation

- **Migrations** : `alembic upgrade head` (lancé automatiquement au démarrage du conteneur).
  Après toute modification de `domain/models.py` : `alembic revision --autogenerate -m "…"`,
  relire le fichier généré, puis vérifier `alembic check`.
- **Worker** : un seul `python worker.py` (service `worker` de docker-compose).
- **Catalogue** : `python -m scripts.load.taxonomy [--dry-run]` (idempotent).
- **Comptes** : `python create_user.py --email … --password … [--organisation <slug>] [--nom-organisation …]
  [--role admin|gestionnaire|technicien|lecteur] [--superadmin]` (organisation `defaut` si non précisée,
  créée si absente ; rôle `admin` par défaut).
- **Sondes** : `/api/v1/health/live` (processus) et `/api/v1/health/ready` (base).
- **Qualité** : `ruff check .` et `pytest --cov=…` (seuil CI : 85 %). La CI rejoue les tests et
  les migrations sur PostgreSQL et audite les dépendances.

## 7. Dépannage

| Symptôme | Cause probable |
|---|---|
| L'API refuse de démarrer : « SECRET_KEY trop courte » | Générer une clé de 64 caractères hexadécimaux |
| 401 alors que l'utilisateur vient de se connecter | Cookie `Secure` sur une origine HTTP autre que localhost : `COOKIE_SECURE=false` en local |
| 403 « protection CSRF » | Requête par cookie sans en-tête `X-Requested-With` |
| 429 sur la connexion | Limitation de débit : attendre la durée de `Retry-After` |
| Tableau de bord « En attente » | Aucun passage du worker encore : `python -m infrastructure.jobs.mise_a_jour_capteurs` |
| `Can't locate revision ab36bd25cc59` | Base créée avant la migration v1 : recréer la base de développement |
| Avertissement « RLS inopérante » au démarrage | L'API se connecte en superutilisateur : créer le rôle applicatif (`exploitation.md`) |
| 403 « Permissions insuffisantes » | Rôle insuffisant pour l'action (lecteur, technicien) : à changer par un admin de l'organisation |
| Requêtes SQL manuelles sans résultat (rôle applicatif) | Normal sous RLS : `SELECT set_config('app.organisation_id', '<id>', false)` ou `set_config('app.contourner_rls', 'on', false)` dans la session psql |
