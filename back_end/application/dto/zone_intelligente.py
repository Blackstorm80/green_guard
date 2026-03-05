from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class NiveauZone(str, Enum):
    GLOBALE = "globale"
    VILLE = "ville"
    QUARTIER = "quartier"
    PRECIS = "precis"

class ZoneIntelligenteDTO(BaseModel):
    id: str = Field(..., description="Identifiant unique de la zone")
    nom: str = Field(..., description="Nom lisible de la zone")
    niveau: NiveauZone = Field(..., description="Granularité du clustering")
    sante_percent: float = Field(..., ge=0, le=100, description="Santé 0-100%")
    nb_espaces: int = Field(..., ge=0, description="Nombre d'espaces")
    nb_ok: int = Field(..., ge=0, description="Espaces OK")
    nb_warning: int = Field(..., ge=0, description="Espaces warning") 
    nb_critique: int = Field(..., ge=0, description="Espaces critiques")
    centroid_lat: float = Field(..., description="Latitude centroïde")
    centroid_lon: float = Field(..., description="Longitude centroïde")
    couleur_gauge: str = Field(..., description="Couleur hexadécimale")
    rayon_km: Optional[float] = Field(None, description="Rayon zone en km")