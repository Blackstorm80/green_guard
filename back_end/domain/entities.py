# Fichier : domain/entities.py

from dataclasses import dataclass
import datetime


@dataclass
class EspaceVertEntity:
    """
    Entité métier pour un espace vert.
    Objet pur, sans dépendance ORM ou API.
    """
    id: int
    nom: str
    localisation: str | None = None
    reserve_utile_max: float
    coefficient_cultural: float


@dataclass
class BilanHydriqueJournalierEntity:
    """
    Entité métier représentant le bilan hydrique pour un jour donné.
    Objet pur, sans dépendance à l'ORM.
    """
    id: int
    date: datetime.date
    reserve_eau: float
    indice_stress: float
    statut_hydrique: str
    espace_id: int



@dataclass
class UtilisateurEntity:
    """Entité métier représentant un utilisateur pouvant gérer un ou plusieurs espaces verts."""
    id: int
    nom: str
    email: str
    role: str  # "gerant" ou "super_admin"

