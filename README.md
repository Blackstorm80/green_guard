

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

* **Clustering DBSCAN** : Regroupement automatique des points par densité géographique pour éviter la surcharge visuelle du Dashboard.
    * *Configuration cible* : `distance_max = 0.02` (Epsilon) pour une granularité précise par quartier.
* **KPIs Temps Réel** : Agrégation des données de santé et d'humidité pour fournir des moyennes globales (Santé de la flotte, Stress hydrique critique).
## Sécurité et Environnement

* Aucun secret n'est versionné : les fichiers `.env` sont ignorés par git et la CI (`.github/workflows/securite.yml`) échoue si un `.env`, une base SQLite ou `node_modules` est commité, et lance un scan **gitleaks**.
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
cp .env.example .env       # puis renseigner SECRET_KEY
alembic upgrade head
uvicorn main:app --reload
```
*Accès Swagger : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*

### 3. Frontend
```bash
cd front_end
npm install
cp .env.example .env.local
npm run dev
```

### 4. Créer un administrateur
```bash
cd back_end
python create_user.py --email <email> --password <mot_de_passe>
```

---
Plan de reprise et feuille de route v1.0 : [`PLAN_ARCHITECTE_2026-10-03.md`](PLAN_ARCHITECTE_2026-10-03.md)

*Développé pour une gestion durable des ressources urbaines.*
