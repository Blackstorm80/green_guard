# back_end/application/dto/intervention.py
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import List


class PrioriteIntervention(str, Enum):
    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"


class TypeIntervention(str, Enum):
    STRESS_HYDRIQUE = "stress_hydrique"
    HYPERCAPNIE = "hypercapnie"
    CANICULE = "canicule"
    MAINTENANCE = "maintenance"


class InterventionUrgenteDTO(BaseModel):
    id: int
    espace_id: int
    espace_nom: str
    type: TypeIntervention
    label: str  # "Sec", "CO₂", "Chaleur"
    description: str
    priorite: PrioriteIntervention
    created_at: datetime
    is_read: bool = False


class InterventionsUrgentesDTO(BaseModel):
    interventions: List[InterventionUrgenteDTO]
    total: int
    non_lues: int