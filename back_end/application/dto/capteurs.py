from datetime import datetime

from pydantic import BaseModel, ConfigDict

from application.dto.meteo import MeteoDTO


class LectureCapteurDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    espace_id: int
    nom: str
    temperature_c: float | None = None
    humidite_percent: float | None = None
    humidite_air_percent: float | None = None
    co2_ppm: float | None = None
    reserve_eau_mm: float | None = None
    sante_percent: float | None = None
    statut: str
    timestamp: datetime | None = None


class MetriquesDashboardDTO(BaseModel):
    sante_globale_percent: float | None = None
    espaces_suivis: int
    espaces_avec_donnees: int
    espaces_stress: int
    espaces_critiques: int
    co2_moyen_ppm: float | None = None
    qualite_air: str


class DashboardCapteursDTO(BaseModel):
    statut: str    # "Sain" | "Attention" | "Critique" | "En attente"
    message: str
    meteo_exterieure: MeteoDTO | None = None
    capteurs: list[LectureCapteurDTO]
    metrics: MetriquesDashboardDTO
