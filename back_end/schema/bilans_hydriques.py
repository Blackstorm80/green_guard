from datetime import date

from pydantic import BaseModel, ConfigDict


class BilanHydriqueRead(BaseModel):
    """Bilan d'une journée et ses termes (mm, sauf coefficients) ; termes à None avant le modèle FAO-56."""
    model_config = ConfigDict(from_attributes=True)

    date: date
    statut_hydrique: str
    reserve_utile_fin_journee: float
    indice_stress: float
    et0_mm: float | None = None
    kl: float | None = None
    ks: float | None = None
    etc_mm: float | None = None
    pluie_mm: float | None = None
    pluie_efficace_mm: float | None = None
    arrosage_mm: float | None = None
    drainage_mm: float | None = None
    epuisement_debut_mm: float | None = None
    epuisement_fin_mm: float | None = None
    taw_mm: float | None = None
    raw_mm: float | None = None
    version_modele: str
    source_meteo: str | None = None
