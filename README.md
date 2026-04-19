

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

Le projet intègre le **Secret Scanning**. Tout fichier contenant des clés sensibles (API OpenWeather, JWT Secret) est bloqué au commit.

1.  **Fichier .env** : Doit être créé localement dans /back_end.
2.  **Exemple de configuration** :
    ```env
    DATABASE_URL=sqlite:///./database.db
    SECRET_KEY=votre_cle_jwt_super_secrete
    OPENWEATHER_API_KEY=votre_cle_openweather
    ```

## Workflow de Contribution

1.  **Branchement** : Ne jamais travailler sur main. Créez une branche feature/ ou fix/.
2.  **Pull Request** : La fusion nécessite une validation de la cohérence avec le cœur métier.
3.  **Conflits** : En cas de conflit lors d'un pull sur main, priorité absolue est donnée à la version locale pour préserver l'architecture du Dashboard.

## Lancement Rapide

### 1. Backend
```bash
cd back_end
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate sur Windows
pip install -r requirements.txt
uvicorn main:app --reload
```
*Accès Swagger : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)*

### 2. Frontend
```bash
cd front_end
npm install
npm run dev
```

### 3. Initialisation DB (DBeaver)
Pour activer les clusters, exécutez ce SQL :
```sql
INSERT INTO clustering_configs (nom_config, distance_max, algorithme)
VALUES ('Standard_DBSCAN', 0.02, 'DBSCAN');
```

---
*Développé pour une gestion durable des ressources urbaines.*