# Fichier : domain/entities.py

from dataclasses import dataclass
import datetime
from typing import Optional


@dataclass
class EspaceVertEntity:
    """
    Entité métier représentant un espace vert.
    Décrit le contexte réel où une plante va vivre.
    """
    id: int
    nom: str
    type_espace: str             # "toiture", "parc", "jardin", etc.
    localisation: str            # ou une structure plus riche (coordonnées)

    # Lien vers le catalogue de plantes
    plante_id: int               # id de PlanteEntity choisie pour cet espace

    # Caractéristiques physiques / environnementales de l'espace
    surface_m2: float
    exposition_reelle: str       # "Soleil" | "Mi-ombre" | "Ombre"
    type_sol: str                # "sableux", "limoneux", "argileux", ...
    ph_sol: Optional[float] = None

    # Paramètres hydriques du sol de l'espace
    reserve_utile_max: float
    coefficient_cultural: float

    # Métadonnées de gestion
    zone: Optional[str] = None
    gerant_id: Optional[int] = None


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


@dataclass
class PlanteEntity:
    """Entité métier représentant une plante du catalogue."""
    id: int
    nom_scientifique: str
    nom_commun: str
    type_plante: str              # arbre, arbuste, vivace, couvre-sol, etc.

    # Eau
    besoin_eau: str               # "Faible" | "Moyen" | "Élevé" (pour le front)
    eau_min_mm_semaine: float
    eau_max_mm_semaine: float

    # Température (homéostasie)
    temp_min_confort: float       # zone de confort
    temp_max_confort: float
    temp_min_survie: float        # limites absolues
    temp_max_survie: float

    # Lumière
    exposition: str               # "Soleil" | "Mi-ombre" | "Ombre"

    # Sol
    type_sol_prefere: str         # "sableux", "limoneux", "argileux", ...
    ph_min: Optional[float] = None
    ph_max: Optional[float] = None

    # UI / descriptions
    icone: Optional[str] = None
    description_courte: Optional[str] = None