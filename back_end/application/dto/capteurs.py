# back_end/application/dto/capteurs.py
from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class LectureCapteurDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    espace_id: int
    temperature_c: float
    humidite_percent: float
    luminosite_lux: int
    co2_ppm: int
    o2_percent: float
    reserve_eau_mm: float
    timestamp: str


class DashboardCapteursDTO(BaseModel):
    meteo_exterieure: Optional[dict]  # MeteoDTO
    capteurs: List[LectureCapteurDTO]
    metrics: dict