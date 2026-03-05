# Fichier: domain/logic/clustering.py
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from typing import List
from sqlalchemy.orm import Session

# IMPORTS DÉFINITIFS - TOUT ICI
from domain.entities import EspaceVertEntity, ZoneIntelligenteEntity
from domain.entities.clustering_config import ClusteringConfigEntity



""" l'algorithme a été dev a partir de celui de https://fr.python-3.com/?p=4563 , qui a servi de base d'apprentissage et de comprenhension pour coder mon clusturing "  """
def calculer_features_espaces(espaces: List[EspaceVertEntity]) -> np.ndarray:
    """Extrait et normalise les features pour K-Means."""
    features = []
    
    for espace in espaces:
        # 1. Géolocalisation (prioritaire)
        lat, lon = 0.0, 0.0
        if espace.localisation:
            try:
                lat = float(espace.localisation.split(',')[0])
                lon = float(espace.localisation.split(',')[1])
            except (ValueError, IndexError):
                pass # Garde lat/lon à 0 si le format est incorrect
        
        # 2. Santé (sur 7 derniers jours, avec une valeur par défaut robuste)
        sante_7j = getattr(espace, 'sante_moyenne_7j', 85.0) or 85.0
        
        # 3. Caractéristiques structurelles (encodage simple)
        type_espace_code = {"parc": 1, "jardin": 2, "square": 3, "rue": 4}.get(
            espace.type_espace.lower() if espace.type_espace else "square", 3
        )
        
        # 4. Variance santé (stabilité, avec une valeur par défaut)
        variance_sante = getattr(espace, 'variance_sante_7j', 5.0) or 5.0
        
        features.append([lat, lon, sante_7j/100, type_espace_code, variance_sante])
    
    #  pour que K-Means traite toutes les features équitablement
    scaler = StandardScaler()
    return scaler.fit_transform(features)

def creer_noms_zones_paris(centroids: np.ndarray, granularite: str) -> List[str]:
    """Génère des noms lisibles pour les zones (spécifique Paris pour la démo)."""
    noms = []
    arrondissements_paris = [
        "1er", "2e", "3e", "4e", "5e", "6e", "7e", "8e", "9e", 
        "10e", "11e", "12e", "13e", "14e", "15e", "16e", "17e", "18e", "19e", "20e"
    ]
    
    for i, centroid in enumerate(centroids):
        # Logique simple pour associer un centroïde à un arrondissement pour le nom
        # Note: ceci est une approximation pour juste pour la demo , jesuis encours d'apprentissage car le sujet est legerment complex .
        arrdt_index = int(abs(centroid[0] * centroid[1] * 100)) % len(arrondissements_paris)
        
        if granularite == "quartier":
            noms.append(f"Quartier {arrondissements_paris[arrdt_index]}-{i+1}")
        else:
            noms.append(f"Zone {arrondissements_paris[arrdt_index]} (Z{i+1})")
    
    return noms

def executer_clustering_intelligent(
    db: Session,
    user_id: int
):
    # Retire complètement -> List[ZoneIntelligenteEntity]
    # Garde le reste de ton code IDENTIQUE

    """
    Exécute le clustering complet :
    1. Lit la config utilisateur.
    2. Récupère les espaces et calcule les features.
    3. Exécute K-Means et calcule le score de silhouette.
    4. Persiste les nouvelles zones et leurs métriques.
    """
    config = db.query(ClusteringConfigEntity).filter(ClusteringConfigEntity.user_id == user_id).first()
    if not config:
        raise ValueError("Aucune config de clustering trouvée pour cet utilisateur")
    
    espaces = db.query(EspaceVertEntity).filter(EspaceVertEntity.gerant_id == user_id).all()
    if len(espaces) < config.n_clusters:
        raise ValueError("Pas assez d'espaces à clusteriser pour le nombre de clusters configuré")
    
    X = calculer_features_espaces(espaces)
    
    kmeans = KMeans(n_clusters=config.n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    from sklearn.metrics import silhouette_score
    silhouette = silhouette_score(X, labels)
    
    # Nettoyage des anciennes zones pour ce user
    db.query(ZoneIntelligenteEntity).filter(ZoneIntelligenteEntity.user_id == user_id).delete()
    db.commit()
    
    nouvelles_zones = []
    noms_zones = creer_noms_zones_paris(kmeans.cluster_centers_, config.granularite)
    
    for i in range(config.n_clusters):
        indices_cluster = [j for j, label in enumerate(labels) if label == i]
        if not indices_cluster: continue

        espaces_cluster = [espaces[j] for j in indices_cluster]
        sante_moyenne = np.mean([getattr(e, 'sante_percent', 85.0) or 85.0 for e in espaces_cluster])
        
        zone = ZoneIntelligenteEntity(
            nom=noms_zones[i],
            user_id=user_id,
            centroid_lat=float(kmeans.cluster_centers_[i][0]),#parametre de compraison pour creer les clusters
            centroid_lon=float(kmeans.cluster_centers_[i][1]),#param de comparaison pour creer les clusters
            rayon_km=config.rayon_max_km,
            sante_moyenne=float(sante_moyenne),
            nb_espaces=len(espaces_cluster),
            granularite=config.granularite,
            silhouette_score=float(silhouette)
        )
        db.add(zone)
        db.flush()
        
        """for espace in espaces_cluster:
            liaison = ZoneEspaceEntity(
                zone_id=zone.id,
                espace_id=espace.id,
                distance_centroid_km=0.0, # Pourrait être calculé avec haversine
                poids=1.0 / len(espaces_cluster)
            )
            db.add(liaison)"""
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