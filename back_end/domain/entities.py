# Fichier : domain/entities.py

from dataclasses import dataclass
import datetime


@dataclass
class EspaceVertEntity:
    """
    Entité métier représentant un espace vert.
    C'est un objet pur, sans aucune dépendance à l'ORM ou à la base de données.
    """
    id: int
    nom: str
    localisation: str | None  # ex. "lat, lon"
    type_espace: str  # pelouse, massif, arbre isolé, etc.
    type_sol: str  # riche / moyen / pauvre, ou argileux / sableux / limoneux
    reserve_utile_max: float  # (mm)
    coefficient_cultural: float  # (Kc, besoin relatif en eau)
    surface_m2: float | None = None  # pour plus tard (volume en litres, etc.)


@dataclass
class BilanHydriqueJournalierEntity:
    """
    Entité métier représentant le bilan hydrique pour un jour donné.
    Objet pur, sans dépendance à l'ORM.
    """
    id: int
    date: datetime.date
    reserve_eau: float  # (mm dans le sol)
    indice_stress: float  # (0 à 1)
    statut_hydrique: str  # ("Confort", "A surveiller", "Critique")
    espace_id: int  # (clé vers l’espace vert)
    duree_stress_cumule: float | None = None  # pour plus tard


@dataclass
class UtilisateurEntity:
    """Entité métier représentant un utilisateur."""
    id: int
    nom: str
    email: str
    role: str # ex: "gerant", "admin"