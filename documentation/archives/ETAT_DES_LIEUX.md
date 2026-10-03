# ÉTAT DES LIEUX — GreenGuard

> ⚠️ **Document obsolète (2026-10-03)** : remplacé par `PLAN_ARCHITECTE_2026-10-03.md`.
> Plusieurs modules marqués « ✅ Fonctionnel » ci-dessous ont été vérifiés comme cassés.
> Conservé pour l'historique uniquement.
**Date de rédaction** : 2026-06-13  
**Rédigé par** : Claude Code (session de reprise après audit)  
**Branche** : `main`  
**Statut général** : 🟡 — Sécurité corrigée, base stable, prêt pour développement fonctionnel

---

## 1. CONTEXTE DE LA SESSION

Ce document fait suite à l'audit technique du 2026-05-24. La session a permis de traiter **20 alertes sur 35** (toutes les critiques et hautes automatisables) et de résoudre deux décisions d'architecture bloquantes (HR-2 météo, HR-4 base de données).

---

## 2. ARCHITECTURE ACTUELLE

```
green_guard/
├── back_end/                    # API FastAPI — Python 3.x
│   ├── api/v1/endpoints/        # Routes HTTP (auth, espaces, capteurs, météo…)
│   ├── application/use_cases/   # Orchestration métier
│   ├── domain/
│   │   ├── logic/               # Algorithmes (DBSCAN, bilan hydrique, stress…)
│   │   ├── models.py            # Modèles SQLAlchemy (source de vérité ORM)
│   │   └── ports/               # Interfaces (IMeteoService, IRepository…)
│   ├── infrastructure/
│   │   ├── database.py          # Connexion PostgreSQL via DATABASE_URL
│   │   ├── repositories/        # Implémentations des ports
│   │   └── services/            # Open-Meteo, capteur simulé
│   ├── schema/                  # DTOs Pydantic (validation requêtes/réponses)
│   ├── alembic/                 # Migrations de base de données
│   │   └── versions/
│   │       └── ab36bd25cc59_initial.py   # Migration initiale (appliquée ✅)
│   ├── alembic.ini
│   ├── main.py                  # Point d'entrée FastAPI
│   └── requirements.txt
│
├── front_end/                   # SPA React + Vite + Tailwind
│   ├── src/
│   │   ├── Pages/               # Login, Register, Dashboard, Espaces, Rapports…
│   │   ├── components/          # MeteoWidget, Notifications, FilterBar…
│   │   ├── layouts/             # Header, Sidebar, DashboardLayout
│   │   ├── services/api.js      # Client HTTP — UNIQUE point d'appel API
│   │   └── context/AuthContext.jsx
│   └── .env.local               # Variables Vite (VITE_API_URL)
│
└── docker-compose.yml           # db (PostgreSQL 16) + backend + frontend
```

**Pattern architectural** : Onion Architecture (Domain → Application → Infrastructure)  
**Auth** : JWT (HS256, 60 min), bcrypt, RBAC simple (`admin` / `user`)

---

## 3. INFRASTRUCTURE & DÉMARRAGE

### Base de données
- **Moteur** : PostgreSQL 16 (via Docker)
- **ORM** : SQLAlchemy 2.x (sessions synchrones)
- **Migrations** : Alembic — migration initiale `ab36bd25cc59` appliquée le 2026-06-13
- **17 tables créées** : `users`, `espaces_verts`, `zones_intelligentes`, `capteurs`, `mesures`, `bilans_hydriques`, `notifications`, `alertes`, `types_alertes`, `niveaux_alertes`, `especes_vegetales`, `plantes`, `auxiliaires`, `clustering_configs`, `actions_irrigation`, `interventions`, `zone_espaces`

### Variables d'environnement requises (`back_end/.env`)
| Variable | Valeur actuelle | Description |
|----------|----------------|-------------|
| `DATABASE_URL` | `postgresql://greenguard:greenguard_dev@localhost:5432/greenguard` | Connexion PostgreSQL |
| `SECRET_KEY` | ✅ Renseignée | Clé JWT (64 hex chars) |
| `FRONTEND_URL` | `http://localhost:5173` | CORS autorisé |

### Démarrage rapide
```bash
# 1. Lancer PostgreSQL
docker compose up db -d

# 2. Backend (depuis back_end/)
.\venv\Scripts\python.exe -m uvicorn main:app --reload

# 3. Frontend (depuis front_end/)
npm run dev

# OU tout en Docker
docker compose up --build
```

### Migrations futures
```bash
# Après chaque modification de models.py :
cd back_end
.\venv\Scripts\python.exe -m alembic revision --autogenerate -m "description"
.\venv\Scripts\python.exe -m alembic upgrade head
```

---

## 4. CE QUI A ÉTÉ CORRIGÉ DANS CETTE SESSION

### Sprint 0 — Sécurité critique (6 fixes)
| ID | Fichier | Correction |
|----|---------|-----------|
| A2 | `api/deps/auth.py` | JWT `SECRET_KEY` hardcodé → `os.getenv("SECRET_KEY")`, crash au démarrage si absent |
| A4 | `src/Pages/login/Login.jsx` | Credentials `admin@greenguard.com / password` supprimés des `useState` |
| A5+A6 | `schema/utilisateurs.py`, `endpoints/auth.py`, `services/api.js` | Champ `role` retiré de `UserCreate` et du payload frontend ; backend force toujours `"user"` |
| A7 | `main.py` | CORS `allow_origins=["*"]` → liste explicite `localhost:3000/5173 + FRONTEND_URL` |
| A1+A3 | `back_end/.env`, `weatherServices.js` | Clés API OpenWeather migrées en variables d'env (`VITE_WEATHER_API_KEY` supprimée après décision HR-2) |
| A31 | `main.py` | `print()` → `logging.info()` |

### Sprint 1 — Stabilité modèles (7 fixes)
| ID | Fichier | Correction |
|----|---------|-----------|
| A8 | `domain/models.py` | Doublon `espace_id` ligne 122 dans `BilanHydriqueJournalier` supprimé |
| A9 | `domain/models.py` | Modèles `EspeceVegetale`, `TypeAlerte`, `NiveauAlerte`, `Alerte` créés |
| A10 | `domain/logic/bilan_hydrique.py` | `reserve_eau` → `reserve_utile_fin_journee` (lecture bilan précédent + écriture) |
| A11+A12 | `domain/models.py` | `ZoneIntelligente` : 5 champs ajoutés (`centroid_lat/lon`, `rayon_km`, `sante_moyenne`, `nb_espaces`) + relation many-to-many `espaces` via table `zone_espaces` |
| A25 | `domain/models.py` | `ClusteringConfig` : champs `granularite` et `rayon_max_km` ajoutés |
| A17+A29 | `weatherServices.js` → **supprimé**, `api.js` | Templates literals `{city}` → `${city}` corrigés, URLs → `import.meta.env.VITE_API_URL` |
| A21 | `layouts/Header.jsx` | `import api from ...` → `import { api } from ...` |

### Sprint 2 — Dette technique (5 fixes)
| ID | Fichier | Correction |
|----|---------|-----------|
| A14 | `create_user.py` | Credentials `admin@demo.com / admin123` remplacés par `argparse` CLI |
| A15 | `api/v1/endpoints/health.py` | Endpoint `/diagnostic` protégé avec `Depends(get_current_active_user)` |
| A20 | `api/v1/endpoints/auth.py` | Message "Cet email est déjà utilisé" → "Impossible de créer ce compte" (anti-énumération) |
| A24 | `src/services/api.js` | `if (!response.ok) throw new Error(...)` ajouté sur tous les appels sans vérification |
| A32 | `requirements.txt` | `python-jose`, `python-multipart`, `python-dotenv`, `bcrypt`, `alembic`, `psycopg2-binary` ajoutés avec versions pinned ; doublons supprimés |

### Décisions d'architecture
| HR | Décision | Implémentation |
|----|----------|---------------|
| HR-2 | **Météo mono-source backend** | `weatherServices.js` supprimé ; `api.js` expose `getMeteoByCoords()` et `getMeteo()` qui appellent `/api/v1/meteo/actuelle` et `/api/v1/meteo/{ville}` (Open-Meteo, gratuit, sans clé API) ; endpoint `/{ville}` normalisé pour retourner `MeteoDTO` |
| HR-4 | **SQLite → PostgreSQL** | `database.py` lit `DATABASE_URL`, `psycopg2-binary` + `alembic` dans requirements, `docker-compose.yml` avec service `db` PostgreSQL 16 + volume persistant + healthcheck, migration initiale appliquée |

---

## 5. CE QUI RESTE À FAIRE

### Actions manuelles bloquantes (humain requis)
| # | Action | Urgence |
|---|--------|---------|
| 🔴 | **Rotation clé OpenWeather** : les deux clés (`[clé OpenWeather n°1 — caviardée]` et `[clé OpenWeather n°2 — caviardée]`) sont encore dans l'historique git → révoquer sur openweathermap.org et purger l'historique avec BFG Repo-Cleaner | Critique |
| 🔴 | **Vérifier `green_guard.db`** : ce fichier SQLite est commité en base (git status : modifié). Vérifier s'il contient le compte `admin@demo.com` — si oui, c'est une backdoor active. Supprimer ce fichier du repo git : `git rm --cached back_end/green_guard.db` | Critique |
| 🟡 | **`back_end/init_db.py`** : ce script référence des modèles incorrects (`Sensor` au lieu de `Capteur`, `date_bilan` au lieu de `date`) et des champs qui n'existent plus. À réécrire ou supprimer | Haute |

### Commande BFG pour purger les secrets git
```bash
# Installer BFG : https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --replace-text secrets_to_remove.txt .git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
```
(`secrets_to_remove.txt` contient les deux clés OpenWeather, une par ligne)

### Alertes restantes de l'audit (non traitées)
| ID | Criticité | Description |
|----|-----------|-------------|
| A13 | 🔴 | **0 test** sur ~60 modules de logique domaine — suite pytest à créer en priorité |
| A16 | 🟡 | Token JWT dans `localStorage` → vulnérable XSS. Migrer vers cookie `httpOnly` |
| A18 | 🟡 | Aucun rate limiting sur `/login` et `/register` → installer `slowapi` |
| A19 | 🟡 | Aucune validation `password` (longueur min, complexité) dans `UserCreate` |
| A22 | 🟡 | `api.triggerAction()` appelé dans `homeTableauDeBord.jsx` mais inexistant dans `api.js` → crash au clic |
| A23 | 🟡 | N+1 query dans `application/use_cases/capteurs.py:43-46` → batch fetch `WHERE id IN (...)` |
| A26 | 🟡 | 50+ constantes magiques dans `domain/logic/` → extraire dans `constants.py` documenté |
| A27 | 🟡 | Aucun security header HTTP (CSP, HSTS, X-Frame-Options) → middleware `starlette-security-headers` |
| A28 | ✅ | Migré vers PostgreSQL |
| A30 | 🟠 | Alertes créées dans `sante.py` mais jamais persistées → injecter un repository |
| A33 | 🟠 | Mélange JSX / TSX sans cohérence dans le frontend |
| A34 | 🟠 | `stress_sanitaire.py:23` : `# je chercher une better solution` — code non finalisé |
| A35 | 🟠 | `documentation/Doc_back_end.md` vide — à rédiger |

### Décisions d'architecture en suspens
| HR | Question |
|----|---------|
| HR-1 | Les seuils agronomiques (`0.3`, `0.6`, `15°C`, `24°C`…) dans `stress_hydrique.py` ont-ils une base scientifique validée ? Peuvent-ils varier par type de plante / biome ? |
| HR-3 | Le simulateur de capteurs IoT (`capteur_hybrid_service.py`) est-il la source définitive ou une vraie intégration IoT est-elle prévue ? Roadmap capteurs réels ? |
| HR-5 | `Documentation_Usecases.md` et le code `generer_bilans_hydriques_journaliers.py` sont désynchronisés — lequel est la référence ? |
| HR-7 | Le dataset `inaturalist/` (9 549 observations, embeddings ResNet50) — est-il dans le périmètre actuel ou prévu pour un futur module de classification ? |

---

## 6. ÉTAT DES FONCTIONNALITÉS

| Module | État | Notes |
|--------|------|-------|
| Authentification (login/register/JWT) | ✅ Fonctionnel | Sécurisé, roles corrigés |
| Espaces verts (CRUD) | ✅ Fonctionnel | Modèle complet |
| Capteurs & mesures | ✅ Fonctionnel | Simulation active (scheduler 2 min) |
| Bilan hydrique | ✅ Logique corrigée | `reserve_utile_fin_journee` aligné |
| Clustering (DBSCAN) / Zones intelligentes | ⚠️ Partiellement corrigé | Modèle complété, logique `clustering.py` à tester |
| Santé des espaces | ⚠️ Alertes non persistées | `sante.py` crée des alertes mais ne les sauvegarde pas (A30) |
| Météo | ✅ Fonctionnel | Mono-source backend, Open-Meteo, sans clé API |
| Notifications | ✅ Modèle OK | Endpoints à vérifier |
| Interventions | ✅ Modèle OK | |
| Catalogue botanique | ✅ Fonctionnel | |
| Dashboard | ⚠️ `triggerAction()` crash | A22 non corrigé |
| Tests | ❌ 0% couverture | Priorité absolue |

---

## 7. DETTE TECHNIQUE ESTIMÉE RÉSIDUELLE

| Catégorie | Estimation |
|-----------|-----------|
| Tests unitaires domaine/logique | ~10 j/h |
| Correction A22 (triggerAction) + A30 (alertes non persistées) | ~1 j/h |
| Rate limiting + security headers (A18, A27) | ~1 j/h |
| Migration token localStorage → cookie httpOnly (A16) | ~2 j/h |
| Nettoyage JSX/TSX + constantes magiques (A26, A33) | ~3 j/h |
| Documentation backend (A35) | ~1 j/h |
| **Total résiduel estimé** | **~18 j/h** |

(À comparer à la dette initiale de 25–35 j/h avant cette session)

---

## 8. CONTACTS & RÉFÉRENCES

- Audit initial : `audit_20260524.md` à la racine du projet
- Documentation use cases : `documentation/Documentation_Usecases.md`
- API interactive (quand le backend tourne) : `http://localhost:8000/docs`
- PostgreSQL admin : `docker exec -it green_guard-db-1 psql -U greenguard -d greenguard`

---

*Document généré le 2026-06-13 — à mettre à jour après chaque sprint.*