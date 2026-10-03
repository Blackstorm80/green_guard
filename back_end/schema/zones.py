from pydantic import BaseModel


class ZoneIntelligenteRead(BaseModel):
    id: int
    nom: str
    sante_moyenne: float | None = None
    nb_espaces: int
    centroid_lat: float | None = None
    centroid_lon: float | None = None
    rayon_km: float | None = None
    granularite: str | None = None
    couleur_gauge: str


class ReconstructionZonesRead(BaseModel):
    message: str
    zones: list[str]
