# Fichier : schemas/espaces_verts.py

from pydantic import BaseModel, ConfigDict

class EspaceVertBase(BaseModel):
    """Schéma de base pour un espace vert, avec les champs communs."""
    nom: str
    localisation: str | None = None # Ex: "48.8566, 2.3522"
    reserve_utile_max: float
    coefficient_cultural: float

class EspaceVertCreate(EspaceVertBase):
    """Schéma utilisé pour la création d'un nouvel espace vert via l'API."""
    pass

class EspaceVertRead(EspaceVertBase):
    """Schéma utilisé pour lire et retourner les données d'un espace vert depuis l'API."""
    id: int

    # Permet à Pydantic de lire les données depuis un modèle SQLAlchemy
    model_config = ConfigDict(from_attributes=True)