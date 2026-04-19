
# Documentation Technique Back-End - GreenGuard

## 1. Architecture Logicielle
Le système est construit sur le modèle de l'**Architecture Oignon (Onion Architecture)**. Ce choix garantit que la logique métier est indépendante des frameworks, de l'interface utilisateur et de la base de données.

### Couches du système
* **Domaine (Cœur)** : Contient les entités métier, les modèles SQLAlchemy et la logique pure (calculs, algorithmes).
* **Infrastructure** : Gère la persistance des données (Repositories) et les services externes (Adapteurs API Météo).
* **Application (API)** : Définit les points d'entrée (Endpoints) via FastAPI et les contrats d'échange (Schémas Pydantic).

---

## 2. Structure du Projet

```text
back_end/
├── api/v1/endpoints/   # Contrôleurs FastAPI par domaine (auth, espaces, capteurs)
├── domain/
│   ├── logic/          # Algorithmes de clustering, santé et bilan hydrique
│   ├── models.py       # Définition des tables de la base de données
│   ├── entities.py     # Classes métier pures
│   └── ports/          # Interfaces pour les services externes
├── infrastructure/
│   ├── repositories/   # Implémentations concrètes de l'accès aux données
│   └── services/       # Implémentations des services tiers (Météo)
└── schemas/            # Modèles de validation de données (Pydantic)
```

---

## 3. Composants Algorithmiques

### Clustering Spatial (DBSCAN)
Le système gère l'affichage de plus de 200 capteurs grâce à l'algorithme DBSCAN.
* **Localisation** : `domain/logic/clustering.py`
* **Fonctionnement** : Groupe les capteurs par densité géographique pour éviter la surcharge de l'interface.
* **Paramètre Clé** : `distance_max` (Epsilon) réglé à 0.02 pour une précision à l'échelle du quartier.

### Calcul du Score de Santé
Le score de santé est calculé par une pondération des données de télémétrie.
* **Localisation** : `domain/logic/sante.py`
* **Facteurs** : Humidité du sol, température et historique d'arrosage.

### Bilan Hydrique
Détermine le besoin en eau en fonction de l'évapotranspiration et des précipitations.
* **Localisation** : `domain/logic/bilan_hydrique.py`

---

## 4. Sécurité et Authentification

### Gestion des accès
* **Mécanisme** : OAuth2 avec jetons JWT (JSON Web Tokens).
* **Routes** : `/api/v1/auth/auth/register` pour l'inscription et `/api/v1/auth/auth/login` pour l'authentification.
* **Rôles** : Support des rôles 'admin' et 'user' pour la restriction des endpoints.

### Protection des données
Le fichier `.env` à la racine du dossier `back_end` contient les secrets (SECRET_KEY, API_KEYS). Ce fichier est exclu du contrôle de version.

---

## 5. Base de Données

* **Moteur** : SQLite (environnement de développement).
* **ORM** : SQLAlchemy.
* **Initialisation** : La configuration du clustering doit être injectée manuellement dans la table `clustering_configs` pour activer les fonctions de regroupement.

---

## 6. Maintenance et Évolution

### Ajout d'une fonctionnalité métier
1. Définir l'entité dans `domain/entities.py`.
2. Créer le modèle dans `domain/models.py`.
3. Implémenter la logique dans `domain/logic/`.
4. Exposer via un nouvel endpoint dans `api/v1/endpoints/`.

### Modification des paramètres IA
Toute modification de la sensibilité du clustering ou des seuils de santé doit être effectuée directement dans les fichiers de la couche `domain/logic/`.


1. Précision sur le format des requêtes (Authentication)

Il est crucial de noter que ton API utilise deux formats de données différents, ce qui est une source d'erreur fréquente :

    Login : Reçoit des données au format application/x-www-form-urlencoded (standard OAuth2).

    Register et reste de l'API : Reçoit et envoie du application/json.

2. Le cycle de vie des données de Télémétrie

Puisque tu as 200 espaces, il faut préciser comment le backend gère les performances :

    Agrégation : Le backend ne doit pas renvoyer 200 objets complets pour le Dashboard, mais un résumé (KPIs) calculé via les fonctions de la couche domain/logic/sante.py.

    Calcul à la volée : Le score de santé n'est pas stocké de manière statique, il est recalculé lors de l'appel à l'endpoint pour garantir la fraîcheur des données météo.

3. Guide de dépannage rapide (Troubleshooting)

Ajoute cette section courte pour résoudre les blocages que nous avons rencontrés :

Erreurs courantes :

    401 Unauthorized : Vérifier que le token JWT est bien présent dans le header Authorization: Bearer <token>.

    Clusters vides : Vérifier que la table clustering_configs n'est pas vide dans SQLite (à vérifier via DBeaver).

    Échec de l'inscription : Vérifier que l'email n'existe pas déjà dans la table users



---

## 7. Guide d'Exploitation et Maintenance (Back-end)

### Gestion de la Base de Données
Le projet utilise SQLAlchemy comme ORM. En phase de développement, la base SQLite est auto-générée.
* **Recréation de la base** : Supprimer le fichier `database.db` et relancer le serveur FastAPI. Les tables seront recréées à partir des modèles définis dans `domain/models.py`.
* **Migration** : Pour toute modification de colonne ou ajout de table en production, l'utilisation d'Alembic est préconisée pour gérer l'historique des versions.

### Tests de la Logique Métier
La logique située dans `domain/logic/` est découplée de l'API. Elle peut être testée de manière isolée :
* **Tests unitaires** : Prioriser le test de l'algorithme de clustering (`clustering.py`) et du calcul du bilan hydrique.
* **Validation des seuils** : Vérifier que les fonctions de `sante.py` retournent bien un score compris entre 0 et 100 pour éviter les erreurs d'affichage en sortie d'API.

### Performance et Scalabilité
* **Pagination** : Actuellement, l'endpoint des espaces verts renvoie la flotte complète. Pour dépasser 500 espaces, une pagination devra être implémentée dans les `repositories`.
* **Cache** : Les calculs de santé et de clustering étant gourmands en ressources, l'implémentation d'un cache (type Redis ou cache interne Python) sur les endpoints de télémétrie est recommandée pour les appels fréquents.

### Déploiement (Production)
1. **Serveur WSGI** : Utiliser `gunicorn` avec des workers `uvicorn` pour la gestion des processus en production.
2. **Reverse Proxy** : Placer le serveur derrière Nginx pour la gestion du SSL et de la compression.
3. **Logs** : Surveiller les sorties via un logger standard pour capturer les erreurs de connexion aux API météo tierces.

---

### État final de ton projet
Ton projet est maintenant documenté sur tous les aspects critiques :
1. **Installation** (Comment le lancer)
2. **Architecture Oignon** (Comment c'est structuré)
3. **Algorithmes** (Comment fonctionne l'IA de clustering et la santé)
4. **Sécurité** (Comment sont gérés les accès et les secrets)
5. **Maintenance** (Comment faire évoluer le système)

**Est-ce que tu souhaites que je génère un fichier final récapitulatif structuré (par exemple un PDF ou un texte complet à copier-coller) ou as-tu une autre partie du code à corriger ?**