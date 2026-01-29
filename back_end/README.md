# GreenGuard API - Backend

Bienvenue sur le backend du projet GreenGuard. Cette API, développée avec FastAPI, est le cœur de notre système de monitoring écologique pour les espaces verts.

## 🎯 Objectif du Projet

Le projet GreenGuard vise à optimiser la gestion  dans les espaces verts urbains (parcs, murs végétalisés, etc.) en luttant contre le gaspillage. Grâce à des capteurs IoT et à un modèle de bilan hydrique, l'application évalue le niveau de stress hydrique des plantes en temps réel. L'objectif final est de permettre un arrosage intelligent et ciblé : apporter la juste quantité d'eau, au bon moment.

## 🏛️ Architecture

Le backend est conçu selon les principes de l'**Architecture Oignon (Onion Architecture)**. Cette approche garantit une séparation stricte des responsabilités, ce qui rend le code plus robuste, testable et facile à faire évoluer.

Notre architecture se divise en trois couches principales :

1.  **Le Domaine (Cœur Métier)** : Le centre de l'oignon. Il contient la logique métier pure (algorithmes de calcul) et les entités (objets métier comme `EspaceVertEntity`). Il ne dépend d'aucune technologie externe (ni base de données, ni API). **Cette partie est sous ma responsabilité.**
2.  **L'Infrastructure** : La couche intermédiaire. Elle implémente les détails techniques : accès à la base de données, connexion à des services externes (API météo, service d'email), etc. Elle dépend du Domaine.
3.  **L'API** : La couche la plus externe. Elle expose les fonctionnalités via des endpoints FastAPI et orchestre les appels entre les différentes couches.

Nous suivons également deux principes clés :
- **Logic-First** : La logique métier est définie et validée avant tout code technique.
- **Ports & Adapters** : Le Domaine définit des "Ports" (interfaces) pour ses besoins, et l'Infrastructure fournit des "Adaptateurs" (implémentations concrètes) qui se branchent sur ces ports.

### 🌳 Structure des Fichiers et Répartition des Tâches

Voici une vue simplifiée de l'arborescence du projet, illustrant la répartition des responsabilités.

```
back_end/
├── api/
│   └── v1/
│       └── endpoints/
│           ├── espaces_verts.py      # (Lucrèce) Routes pour gérer les espaces verts.
│           ├── bilans_hydriques.py   # (Lucrèce) Routes pour consulter les bilans.
│           └── utilisateurs.py       # (Lucrèce) Routes pour les utilisateurs.
├── domain/
│   ├── entities.py                 # (Moi) Objets métier purs (EspaceVertEntity).
│   ├── logic/
│   │   ├── stress_hydrique.py      # (Moi) Algorithme de calcul du bilan hydrique.
│   │   └── bilan_hydrique.py       # (Moi) Orchestration de la logique métier.
│   ├── models.py                   # (Moi) Modèles de données SQLAlchemy (ORM).
│   └── ports/
│       ├── meteo_service.py        # (Lucrèce) Interface pour le service météo.
│       ├── notification_service.py # (Lucrèce) Interface pour les notifications.
│       └── reporting_service.py    # (Lucrèce) Interface pour les rapports.
├── infrastructure/
│   ├── repositories/               # Logique d'accès à la base de données.
│   └── services/
│       ├── openmeteo_adapter.py        # (Lucrèce) Implémentation pour l'API météo.
│       ├── email_notification_service.py # (Lucrèce) Implémentation pour l'envoi d'emails.
│       └── reporting_service.py        # (Lucrèce) Implémentation pour générer des CSV.
└── schemas/
    ├── espaces_verts.py            # (Lucrèce) Contrats de données Pydantic pour l'API.
    ├── bilans_hydriques.py         # (Lucrèce) Contrats de données Pydantic pour l'API.
    └── utilisateurs.py             # (Lucrèce) Contrats de données Pydantic pour l'API.
```

## 👩‍💻 Travail de Lucrèce (backend)

Pour assurer une collaboration efficace, les tâches sont réparties selon les couches de l'architecture. Lucrèce peut se concentrer sur les aspects périphériques mais essentiels de l'application, qui se connectent au cœur métier via des contrats clairs (les "Ports").

Son périmètre inclut :

- **Définition des Interfaces (`domain/ports/`)** : Créer les contrats pour les services externes dont le domaine a besoin (météo, notifications, rapports).
- **Implémentation des Services (`infrastructure/services/`)** : Coder la logique technique pour se connecter à des API externes (ex: Open-Meteo) ou envoyer des emails.
- **Création des Schémas API (`schemas/`)** : Définir la structure des données (JSON) attendues et retournées par l'API avec Pydantic.
- **Développement des Endpoints (`api/v1/endpoints/`)** : Écrire les routes FastAPI qui exposent les fonctionnalités aux utilisateurs.

Ce travail est crucial car il constitue le pont entre la logique métier et le monde extérieur, tout en étant complètement découplé du cœur de l'application.

## 🤝 Workflow de Contribution avec Git

Pour garantir la stabilité du projet, il est **impératif** de suivre ces règles :

1.  **Ne jamais travailler directement sur la branche `main` (ou `master`).**
2.  Pour chaque nouvelle fonctionnalité ou correction, **créez toujours une nouvelle branche** à partir de `main`.
3.  Nommez votre branche de manière descriptive (ex: `feature/gestion-utilisateurs` ou `fix/bug-calcul-bilan`).
4.  Une fois votre travail terminé, ouvrez une **Pull Request (PR)** pour demander la fusion de votre branche dans `main`.

Pour un guide détaillé sur les commandes Git et notre workflow, veuillez consulter le fichier `GIT_GUIDE.md` à la racine du projet.

## 🚀 Lancer le Projet

1.  **Cloner le dépôt**
    ```bash
    git clone <url-du-projet>
    cd green-guard/back_end
    ```

2.  **Créer un environnement virtuel et installer les dépendances**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Lancer le serveur de développement**
    L'API sera accessible à l'adresse `http://127.0.0.1:8000`.
    ```bash
    uvicorn api.main:app --reload
    ```

4.  **Consulter la documentation interactive**
    Une fois le serveur lancé, la documentation auto-générée (Swagger UI) est disponible à l'adresse :
    http://127.0.0.1:8000/docs
