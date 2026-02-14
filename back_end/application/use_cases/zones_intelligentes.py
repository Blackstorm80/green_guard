from typing import List
from enum import Enum
from dataclasses import dataclass
import math
import random
from collections import defaultdict
from domain.entities.espace_vert import EspaceVertEntity
from domain.ports.espace_vert_repository import IEspaceVertRepository
from application.dto.zone_intelligente import ZoneIntelligenteDTO, NiveauZone

@dataclass
class Coordonnees:
    lat: float
    lon: float

@dataclass
class StatsSante:
    sante_moyenne: float
    nb_ok: int
    nb_warning: int
    nb_critique: int

def creer_zones_intelligentes(
    repo: IEspaceVertRepository,
    current_user_id: int,
    max_zones: int = 8
) -> List[ZoneIntelligenteDTO]:
    """Clustering COMPLET : globale → ville → quartier → K-Means"""
    
    espaces = repo.list_by_user(current_user_id)
    
    if not espaces:
        return []
    
    nb_espaces = len(espaces)
    
    if nb_espaces <= 5:
        return [creer_zone_globale(espaces)]
    elif nb_espaces <= 15:
        return grouper_par_ville(espaces)[:max_zones]
    elif nb_espaces <= 50:
        return grouper_par_rayon(espaces, rayon_km=2.0)[:max_zones]
    else:
        return kmeans_espaces(espaces, k=min(max_zones, nb_espaces//8))

def creer_zone_globale(espaces: List[EspaceVertEntity]) -> ZoneIntelligenteDTO:
    centroid = calculer_centroid(espaces)
    stats = calculer_stats_sante(espaces)
    
    return ZoneIntelligenteDTO(
        id="globale",
        nom=f"Tous vos espaces ({len(espaces)})",
        niveau=NiveauZone.GLOBALE,
        sante_percent=stats.sante_moyenne,
        nb_espaces=len(espaces),
        nb_ok=stats.nb_ok,
        nb_warning=stats.nb_warning,
        nb_critique=stats.nb_critique,
        centroid_lat=centroid.lat,
        centroid_lon=centroid.lon,
        couleur_gauge=determiner_couleur(stats.sante_moyenne)
    )

def grouper_par_ville(espaces: List[EspaceVertEntity]) -> List[ZoneIntelligenteDTO]:
    villes = defaultdict(list)
    for espace in espaces:
        ville = espace.ville.lower() if espace.ville else "inconnu"
        villes[ville].append(espace)
    
    zones = []
    for ville, espaces_ville in villes.items():
        if len(espaces_ville) > 0:
            centroid = calculer_centroid(espaces_ville)
            stats = calculer_stats_sante(espaces_ville)
            zones.append(ZoneIntelligenteDTO(
                id=f"{ville.replace(' ', '-')}",
                nom=f"{ville.title()} ({len(espaces_ville)} espaces)",
                niveau=NiveauZone.VILLE,
                sante_percent=stats.sante_moyenne,
                nb_espaces=len(espaces_ville),
                nb_ok=stats.nb_ok,
                nb_warning=stats.nb_warning,
                nb_critique=stats.nb_critique,
                centroid_lat=centroid.lat,
                centroid_lon=centroid.lon,
                couleur_gauge=determiner_couleur(stats.sante_moyenne)
            ))
    return sorted(zones, key=lambda z: z.nb_espaces, reverse=True)

def grouper_par_rayon(espaces: List[EspaceVertEntity], rayon_km: float = 2.0) -> List[ZoneIntelligenteDTO]:
    """Clustering par rayons de 2km → quartiers naturels"""
    espaces_restant = espaces.copy()
    zones = []
    i = 0
    
    while espaces_restant and len(zones) < 12:
        centre = espaces_restant[0]
        zone_espaces = []
        
        for espace in espaces_restant:
            if distance_km(centre, espace) <= rayon_km:
                zone_espaces.append(espace)
        
        if zone_espaces:
            centroid = calculer_centroid(zone_espaces)
            stats = calculer_stats_sante(zone_espaces)
            zones.append(ZoneIntelligenteDTO(
                id=f"quartier-{i}",
                nom=f"Quartier {i+1} ({len(zone_espaces)} espaces)",
                niveau=NiveauZone.QUARTIER,
                sante_percent=stats.sante_moyenne,
                nb_espaces=len(zone_espaces),
                nb_ok=stats.nb_ok,
                nb_warning=stats.nb_warning,
                nb_critique=stats.nb_critique,
                centroid_lat=centroid.lat,
                centroid_lon=centroid.lon,
                couleur_gauge=determiner_couleur(stats.sante_moyenne),
                rayon_km=rayon_km
            ))
            
            espaces_restant = [e for e in espaces_restant if e not in zone_espaces]
            i += 1
    
    return zones

def kmeans_espaces(espaces: List[EspaceVertEntity], k: int) -> List[ZoneIntelligenteDTO]:
    """K-Means géographique simple (10 itérations)"""
    if k > len(espaces):
        k = len(espaces)
    
    # Initialisation aléatoire des centres
    centres = random.sample(espaces, k)
    
    for iteration in range(10):
        clusters = [[] for _ in centres]
        
        # Assignation aux centres les plus proches
        for espace in espaces:
            distances = [distance_km(espace, centre) for centre in centres]
            cluster_idx = distances.index(min(distances))
            clusters[cluster_idx].append(espace)
        
        # Recalcul des centres
        nouveaux_centres = []
        for cluster in clusters:
            if cluster:
                centroid = calculer_centroid(cluster)
                # Trouve l'espace le plus proche du centroid
                closest_espace = min(cluster, key=lambda e: distance_km_espace_centroid(e, centroid))
                nouveaux_centres.append(closest_espace)
            else:
                nouveaux_centres.append(centres[0])
        
        centres = nouveaux_centres
    
    # Crée les zones finales
    zones = []
    for i, cluster in enumerate(clusters):
        if cluster:
            centroid = calculer_centroid(cluster)
            stats = calculer_stats_sante(cluster)
            zones.append(ZoneIntelligenteDTO(
                id=f"kmeans-{i}",
                nom=f"Cluster {i+1} ({len(cluster)} espaces)",
                niveau=NiveauZone.PRECIS,
                sante_percent=stats.sante_moyenne,
                nb_espaces=len(cluster),
                nb_ok=stats.nb_ok,
                nb_warning=stats.nb_warning,
                nb_critique=stats.nb_critique,
                centroid_lat=centroid.lat,
                centroid_lon=centroid.lon,
                couleur_gauge=determiner_couleur(stats.sante_moyenne),
                rayon_km=None
            ))
    
    return zones

def distance_km(espace1: EspaceVertEntity, espace2: EspaceVertEntity) -> float:
    """Distance Haversine (km)"""
    R = 6371  # Rayon Terre
    lat1, lon1 = math.radians(espace1.latitude), math.radians(espace1.longitude)
    lat2, lon2 = math.radians(espace2.latitude), math.radians(espace2.longitude)
    
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = (math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def distance_km_espace_centroid(espace: EspaceVertEntity, centroid: Coordonnees) -> float:
    dummy_espace = type('Dummy', (), {'latitude': centroid.lat, 'longitude': centroid.lon})()
    return distance_km(espace, dummy_espace)

def calculer_centroid(espaces: List[EspaceVertEntity]) -> Coordonnees:
    if not espaces: return Coordonnees(0, 0)
    lat_moy = sum(e.latitude for e in espaces) / len(espaces)
    lon_moy = sum(e.longitude for e in espaces) / len(espaces)
    return Coordonnees(lat_moy, lon_moy)

def calculer_stats_sante(espaces: List[EspaceVertEntity]) -> StatsSante:
    # Utilise sante_percent si disponible, sinon valeur par défaut
    nb_ok = sum(1 for e in espaces if getattr(e, 'sante_percent', 100) >= 75)
    nb_warning = sum(1 for e in espaces if 50 <= getattr(e, 'sante_percent', 100) < 75)
    nb_critique = sum(1 for e in espaces if getattr(e, 'sante_percent', 100) < 50)
    sante_moyenne = sum(getattr(e, 'sante_percent', 100) for e in espaces) / len(espaces)
    
    return StatsSante(
        sante_moyenne=round(sante_moyenne, 1),
        nb_ok=nb_ok,
        nb_warning=nb_warning,
        nb_critique=nb_critique
    )

def determiner_couleur(sante: float) -> str:
    if sante >= 80:
        return "#10B981"  # Vert
    elif sante >= 60: return "#F59E0B"  # orange
    elif sante >= 40: return "#F97316"  # orange foncé
    else:
        return "#EF4444"  # Rouge