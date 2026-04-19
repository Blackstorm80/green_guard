# Fichier: domain/logic/clustering.py
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from typing import List
from sqlalchemy.orm import Session

# IMPORTS DÉFINITIFS - TOUT ICI
from domain.models import EspaceVert, ZoneIntelligente, ClusteringConfig



""" l'algorithme a été dev a partir de celui de https://fr.python-3.com/?p=4563 , qui a servi de base d'apprentissage et de comprenhension pour coder mon clusturing "  """
def calculer_features_espaces(espaces: List[EspaceVert]) -> np.ndarray:
    """Extrait et normalise les features pour K-Means."""
    features = []
    
    for espace in espaces:
        # 1. Géolocalisation (prioritaire)
        # On utilise directement les champs latitude/longitude du modèle
        lat = getattr(espace, 'latitude', 0.0) or 0.0
        lon = getattr(espace, 'longitude', 0.0) or 0.0
        
        # 2. Caractéristiques structurelles (encodage simple)
        type_espace_code = {"parc": 1, "jardin": 2, "square": 3, "rue": 4}.get(
            espace.type_espace.lower() if espace.type_espace else "square", 3
        )
        
        features.append([lat, lon, type_espace_code])
    
    #  pour que K-Means traite toutes les features équitablement
    scaler = StandardScaler()
    return scaler.fit_transform(features)

def creer_noms_zones_generiques(n_clusters: int, granularite: str) -> List[str]:
    """Génère des noms génériques et non-trompeurs pour les zones."""
    noms = []
    # NOTE: La logique précédente de nommage basée sur les arrondissements était incorrecte
    # car elle créait une fausse corrélation géographique. Une vraie solution
    # nécessiterait un service de reverse-geocoding sur les coordonnées du centroïde.
    # En attendant, nous utilisons un nommage neutre.
    for i in range(n_clusters):
        prefix = "Quartier" if granularite == "quartier" else "Zone"
        if granularite == "quartier":
            noms.append(f"{prefix} Intelligent {i+1}")
        else:
            noms.append(f"{prefix} Intelligente {i+1}")
    return noms

def executer_clustering_intelligent(
    db: Session,
    user_id: int
):
    # Retire complètement -> List[ZoneIntelligente]
    # Garde le reste de ton code IDENTIQUE

    """
    Exécute le clustering complet :
    1. Lit la config utilisateur.
    2. Récupère les espaces et calcule les features.
    3. Exécute K-Means et calcule le score de silhouette.
    4. Persiste les nouvelles zones et leurs métriques.
    """
    config = db.query(ClusteringConfig).filter(ClusteringConfig.user_id == user_id).first()
    if not config:
        raise ValueError("Aucune config de clustering trouvée pour cet utilisateur")
    
    espaces = db.query(EspaceVert).filter(EspaceVert.user_id == user_id).all()
    if len(espaces) < config.n_clusters:
        raise ValueError("Pas assez d'espaces à clusteriser pour le nombre de clusters configuré")
    
    X = calculer_features_espaces(espaces)
    
    kmeans = KMeans(n_clusters=config.n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # Le score de silhouette est une métrique globale pour la qualité du clustering.
    # Il ne doit pas être stocké sur chaque zone individuelle.
    silhouette = silhouette_score(X, labels)
    print(f"Clustering exécuté avec un score de silhouette global de : {silhouette:.4f}")
    
    # Nettoyage des anciennes zones pour cet utilisateur
    db.query(ZoneIntelligente).filter(ZoneIntelligente.user_id == user_id).delete()
    db.commit()
    
    nouvelles_zones = []
    # Utilisation de la nouvelle fonction de nommage générique
    noms_zones = creer_noms_zones_generiques(config.n_clusters, config.granularite)
    
    for i in range(config.n_clusters):
        indices_cluster = [j for j, label in enumerate(labels) if label == i]
        if not indices_cluster: continue

        espaces_cluster = [espaces[j] for j in indices_cluster]
        
        zone = ZoneIntelligente(
            nom=noms_zones[i],
            user_id=user_id,
            centroid_lat=float(kmeans.cluster_centers_[i][0]),
            centroid_lon=float(kmeans.cluster_centers_[i][1]),
            rayon_km=config.rayon_max_km,
            sante_moyenne=None,  # La santé sera calculée par un autre processus
            nb_espaces=len(espaces_cluster),
            granularite=config.granularite
        )
        db.add(zone)
        db.flush()
        
        for espace in espaces_cluster:
            zone.espaces.append(espace)
        
        nouvelles_zones.append(zone)
    
    db.commit()
    return nouvelles_zones

def calculer_couleur_gauge(sante: float) -> str:
    """Détermine la couleur de jauge en fonction du score de santé."""
    if sante >= 85: return "#0CB95D"  # Vert
    if sante >= 65: return "#E77C02"  # Orange
    return "#DF1B1B"  # Rouge