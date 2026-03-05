# Fichier : schemas/espaces_verts.py

from pydantic import BaseModel, ConfigDict
from typing import Optional

class EspaceVertBase(BaseModel):
    """Schéma de base pour un espace vert, avec les champs communs."""
    nom: str
    type_espace: str
    localisation: Optional[str] = None # Ex: "48.8566, 2.3522"
    surface_m2: float
    exposition_reelle: str # ex: "Ensoleillé", "Mi-ombre"
    type_sol: str # ex: "Argileux", "Sableux"
    ph_sol: float
    reserve_utile_max: float
    coefficient_cultural: float
    zone: str # ex: "Zone A"
    gerant_id: int
    plante_id: int

class EspaceVertCreate(EspaceVertBase):
    """Schéma utilisé pour la création d'un nouvel espace vert via l'API."""
    pass

class EspaceVertUpdate(BaseModel):
    """Schéma pour la mise à jour d'un espace vert. Tous les champs sont optionnels."""
    nom: Optional[str] = None
    type_espace: Optional[str] = None
    localisation: Optional[str] = None
    surface_m2: Optional[float] = None
    exposition_reelle: Optional[str] = None
    type_sol: Optional[str] = None
    ph_sol: Optional[float] = None
    reserve_utile_max: Optional[float] = None
    coefficient_cultural: Optional[float] = None
    zone: Optional[str] = None
    gerant_id: Optional[int] = None
    plante_id: Optional[int] = None

class EspaceVert(EspaceVertBase):
    """Schéma utilisé pour lire et retourner les données complètes d'un espace vert."""
    id: int

    # Permet à Pydantic de lire les données depuis un modèle SQLAlchemy
    model_config = ConfigDict(from_attributes=True)