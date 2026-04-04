# back_end/application/dto/vegetal.py
from pydantic import BaseModel
from typing import List

class EtatGlobalVegetalDTO(BaseModel):
    sante_globale_percent: float
    espaces_en_stress: int
    total_espaces: int
    espaces_critique: int
    espaces_warning: int

class DetailZoneImpactDTO(BaseModel):
    zone: str
    oxygen_kg: float
    carbon_kg: float

class ImpactCarboneDTO(BaseModel):
    total_oxygen_kg: float
    total_carbon_absorbed_kg: float
    periode: str
    detail_par_zone: List[DetailZoneImpactDTO]
