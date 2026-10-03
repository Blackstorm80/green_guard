from typing import List, Optional

from pydantic import BaseModel


class ZoneIntelligenteRead(BaseModel):
    id: int
    nom: str
    sante_moyenne: Optional[float] = None
    nb_espaces: int
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    rayon_km: Optional[float] = None
    granularite: Optional[str] = None
    couleur_gauge: str


class ReconstructionZonesRead(BaseModel):
    message: str
    zones: List[str]
