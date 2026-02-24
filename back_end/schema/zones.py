from pydantic import BaseModel, ConfigDict
from typing import List

class ZoneIntelligenteRead(BaseModel):
    id: int
    nom: str
    sante_moyenne: float
    nb_espaces: int
    centroid_lat: float
    centroid_lon: float
    couleur_gauge: str
    granularite: str
    
    model_config = ConfigDict(from_attributes=True)

class ClusteringConfigRead(BaseModel):
    n_clusters: int
    granularite: str
    rayon_max_km: float
