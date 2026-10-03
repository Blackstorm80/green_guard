"""Regroupement géographique des espaces verts (logique pure, sans base de données).

Algorithme : K-Means sur les coordonnées projetées en km (équirectangulaire locale),
ce qui donne des distances homogènes en latitude et en longitude. Les centroïdes
sont recalculés sur les coordonnées réelles des espaces de chaque groupe.
Base d'apprentissage : https://fr.python-3.com/?p=4563
"""
import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans

RAYON_TERRE_KM = 6371.0
COULEUR_INCONNUE = "#64748B"


@dataclass(frozen=True)
class Groupe:
    indices: list[int]           # positions des points dans la liste d'entrée
    centroid_lat: float
    centroid_lon: float
    rayon_km: float              # distance max centroïde → point du groupe


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance orthodromique (haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * RAYON_TERRE_KM * math.asin(math.sqrt(a))


def _projeter_km(points: Sequence[tuple[float, float]]) -> np.ndarray:
    lat_ref = math.radians(sum(p[0] for p in points) / len(points))
    km_par_degre = math.pi * RAYON_TERRE_KM / 180
    return np.array([[lat * km_par_degre, lon * km_par_degre * math.cos(lat_ref)] for lat, lon in points])


def regrouper(points: Sequence[tuple[float, float]], n_groupes: int) -> list[Groupe]:
    """Regroupe des (lat, lon) en au plus n_groupes groupes non vides."""
    if not points:
        return []
    n = max(1, min(n_groupes, len(points)))
    labels = KMeans(n_clusters=n, random_state=42, n_init=10).fit_predict(_projeter_km(points))

    groupes = []
    for label in sorted(set(labels)):
        indices = [i for i, l in enumerate(labels) if l == label]
        lat = sum(points[i][0] for i in indices) / len(indices)
        lon = sum(points[i][1] for i in indices) / len(indices)
        rayon = max(distance_km(lat, lon, *points[i]) for i in indices)
        groupes.append(Groupe(indices=indices, centroid_lat=lat, centroid_lon=lon, rayon_km=round(rayon, 3)))
    return groupes


def nommer_zones(n: int, granularite: str | None) -> list[str]:
    """Noms neutres (un vrai nommage demanderait un géocodage inverse)."""
    prefixe = "Quartier" if granularite == "quartier" else "Zone"
    return [f"{prefixe} {i + 1}" for i in range(n)]


def calculer_couleur_gauge(sante: float | None) -> str:
    """Couleur de jauge selon le score de santé ; gris quand il n'y a pas encore de donnée."""
    if sante is None:
        return COULEUR_INCONNUE
    if sante >= 85:
        return "#0CB95D"
    if sante >= 65:
        return "#E77C02"
    return "#DF1B1B"
