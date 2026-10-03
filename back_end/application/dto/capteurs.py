from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from application.dto.meteo import MeteoDTO


class LectureCapteurDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    espace_id: int
    nom: str
    temperature_c: Optional[float] = None
    humidite_percent: Optional[float] = None
    humidite_air_percent: Optional[float] = None
    co2_ppm: Optional[float] = None
    reserve_eau_mm: Optional[float] = None
    sante_percent: Optional[float] = None
    statut: str
    timestamp: Optional[datetime] = None


class MetriquesDashboardDTO(BaseModel):
    sante_globale_percent: Optional[float] = None
    espaces_suivis: int
    espaces_avec_donnees: int
    espaces_stress: int
    espaces_critiques: int
    co2_moyen_ppm: Optional[float] = None
    qualite_air: str


class DashboardCapteursDTO(BaseModel):
    statut: str    # "Sain" | "Attention" | "Critique" | "En attente"
    message: str
    meteo_exterieure: Optional[MeteoDTO] = None
    capteurs: List[LectureCapteurDTO]
    metrics: MetriquesDashboardDTO
