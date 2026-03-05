# Fichier: application/dto/espace_vert.py
from pydantic import BaseModel
from typing import Optional

class EspaceVertDTO(BaseModel):
    """DTO pour l'affichage d'un espace vert."""
    id: int
    nom: str
    type_espace: str
    localisation: str
    plante_id: int
    surface_m2: float
    exposition_reelle: str
    type_sol: str
    ph_sol: Optional[float]


class CreerEspaceDTO(BaseModel):
    """DTO pour la création d'un nouvel espace vert."""
    nom: str
    type_espace: str
    localisation: str
    plante_id: int
    surface_m2: float
    exposition_reelle: str
    type_sol: str
    ph_sol: Optional[float] = None
    reserve_utile_max: float
    coefficient_cultural: float
    zone: Optional[str] = None
    gerant_id: Optional[int] = None


class MettreAJourEspaceVertDTO(BaseModel):
    nom: Optional[str] = None
    type_espace: Optional[str] = None
    localisation: Optional[str] = None

    plante_id: Optional[int] = None

    surface_m2: Optional[float] = None
    exposition_reelle: Optional[str] = None
    type_sol: Optional[str] = None
    ph_sol: Optional[float] = None

    reserve_utile_max: Optional[float] = None
    coefficient_cultural: Optional[float] = None

    zone: Optional[str] = None
    gerant_id: Optional[int] = None