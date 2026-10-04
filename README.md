

# GreenGuard API - Backend et Intelligence

Bienvenue sur le cœur de **GreenGuard**. Cette API, développée avec FastAPI, orchestre le monitoring écologique, le calcul du bilan hydrique et le clustering spatial pour la gestion intelligente des espaces verts.

## Objectif du Projet

Optimiser la gestion de l'eau en milieu urbain. Grâce à des capteurs IoT et à une logique métier avancée, GreenGuard transforme des données brutes en décisions d'arrosage ciblées pour lutter contre le stress hydrique sans gaspillage.

## Architecture : Le Modèle Oignon

Le projet suit une **Architecture Oignon (Onion Architecture)** pour une séparation stricte des responsabilités et une testabilité maximale.

### Structure des Fichiers et Responsabilités

```text
back_end/
├── api/v1/endpoints/
│   ├── auth.py             # Gestion sécurisée (Login/Register) - JWT
│   ├── espaces_verts.py    # CRUD des sites et espaces
│   └── capteurs.py         # Dashboard et Télémétrie (KPIs)
├── domain/
│   ├── entities.py         # Objets métier purs (EspaceVert, Node)
│   ├── models.py           # Modèles SQLAlchemy (Persistance)
│   ├── logic/
│   │   ├── clustering.py   # IA : Algorithme DBSCAN (Regroupement spatial)
│   │   ├── sante.py        # Calcul des scores de santé globaux
│   │   └── bilan_hydrique.py # Algorithme de stress hydrique
│   └── ports/              # Interfaces (Contrats pour l'infrastructure)
├── infrastructure/
│   ├── repositories/       # Implémentation de l'accès DB
│   └── services/           # Adapteurs (API Météo, Email, Rapports)
└── schemas/                # Contrats Pydantic (Validation API)
```

## Intelligence Spatiale et Performance

Pour gérer la montée en charge (flotte de **200+ espaces verts**), GreenGuard utilise des mécanismes avancés :

* **Zones intelligentes (K-Means géographique)** : regroupement des espaces sur leurs coordonnées projetées en km ; centroïdes et rayons en coordonnées réelles. Nombre de zones paramétrable (`clustering_configs.n_clusters`, 5 par défaut).
* **Bilan hydrique journalier** : calculé chaque heure à partir de la météo réelle (Open-Meteo : ET0 et pluie du jour), de façon idempotente (un bilan par espace et par jour).
* **KPIs** : santé du parc, espaces en stress, qualité de l'air, agrégés à partir des derniers bilans et mesures.

## Sécurité et Environnement

* Aucun secret n'est versionné : les fichiers `.env` sont ignorés par git et la CI (`.github/workflows/securite.yml`) échoue si un `.env`, une base SQLite ou `node_modules` est commité, et lance un scan **gitleaks**.
* **Session** : jeton JWT (PyJWT, HS256, 60 min) dans un cookie `httpOnly` + `SameSite=Lax` + `Secure`, illisible par JavaScript. Toute écriture authentifiée par cookie exige l'en-tête `X-Requested-With` (anti-CSRF). L'en-tête `Authorization: Bearer` reste accepté pour Swagger et les scripts.
* **Protections** : limitation de débit sur la connexion et l'inscription, mot de passe de 12 caractères minimum, `SECRET_KEY` de 32 caractères minimum, en-têtes de sécurité et CSP (API et front), erreurs 500 génériques avec identifiant de requête.
* Chaque dossier fournit un modèle sans valeur réelle à copier :

| Modèle | Copier en | Usage |
|---|---|---|
| `back_end/.env.example` | `back_end/.env` | Lancement local du backend |
| `front_end/.env.example` | `front_end/.env.local` | URL de l'API pour Vite |
| `.env.example` | `.env` (racine) | Variables lues par `docker-compose.yml` |

Générer une clé JWT : `python -c "import secrets; print(secrets.token_hex(32))"`

## Workflow de Contribution

1.  **Branchement** : ne jamais travailler sur `main`. Créez une branche `feature/…`, `fix/…` ou `chore/…`.
2.  **Pull Request** : toute fusion passe par une PR relue, avec la CI au vert.
3.  **Conflits** : résoudre chaque conflit en comprenant les deux versions (jamais de stratégie « tout local » ou « tout distant » aveugle) ; en cas de doute, demander à l'auteur de l'autre modification.
4.  **Schéma de base** : toute modification de `domain/models.py` s'accompagne d'une migration Alembic (`alembic revision --autogenerate -m "…"`).

## Lancement Rapide

### Option A — Toute la pile sous Docker
```bash
cp .env.example .env       # puis renseigner SECRET_KEY et POSTGRES_PASSWORD
docker compose up --build -d
```
Front : http://localhost:3000 — API : http://localhost:8000 (Swagger sur `/docs` si `ENABLE_DOCS=true` dans `.env`). Les migrations s'appliquent au démarrage du backend ; le service `worker` exécute le bilan hydrique toutes les heures (premier passage au démarrage).

> Base créée avant octobre 2026 : le schéma de référence a été remplacé (`0001_schema_v1`).
> Recréer la base de développement : `docker compose down -v` puis `docker compose up --build -d`.

### Option B — Développement local

### 1. Base de données (PostgreSQL via Docker)
```bash
docker compose up db -d
```

### 2. Backend
```bash
cd back_end
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate sur Windows
pip install -r requirements.txt
cp .env.example .env       # puis renseigner SECRET_KEY (ENABLE_SCHEDULER=true : job intégré en dev)
alembic upgrade head
uvicorn main:app --reload
# ou, comme en production : ENABLE_SCHEDULER=false et `python worker.py` dans un second terminal
```
*Accès Swagger : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — nécessite `ENABLE_DOCS=true` dans `back_end/.env` (présent dans `.env.example`)*

### 3. Frontend
```bash
cd front_end
npm install
cp .env.example .env.local
npm run dev
```

### Tests backend
```bash
cd back_end
pip install -r requirements-dev.txt
ruff check .                             # lint (dont règles de sécurité)
pytest --cov=domain --cov=application --cov=api --cov=infrastructure   # SQLite, sans réseau
TEST_DATABASE_URL=postgresql://user:mdp@localhost:5432/base_de_test pytest   # sur PostgreSQL
```

La CI (`.github/workflows/ci.yml`) rejoue tout cela à chaque PR, plus les migrations et la suite sur PostgreSQL, les audits `pip-audit`/`npm audit` et la construction des images.

### 4. Créer un administrateur
```bash
cd back_end
python create_user.py --email <email> --password <mot_de_passe>
```

---
Plan de reprise et feuille de route v1.0 : [`PLAN_ARCHITECTE_2026-10-03.md`](PLAN_ARCHITECTE_2026-10-03.md)

Documentation : [exploitation](documentation/exploitation.md) · [back-end](documentation/Doc_back_end.md) ·
[design system](documentation/design_system.md) · [recette 1.0.0-rc1](documentation/recette_v1.0.0-rc1.md) ·
[journal des versions](CHANGELOG.md)

Tests de bout en bout (pile démarrée) : `cd front_end && npm run test:e2e`

*Développé pour une gestion durable des ressources urbaines.*
