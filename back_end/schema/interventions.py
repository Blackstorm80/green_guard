"""Schémas des interventions terrain (repris du travail de la branche feature/Lucresse-branche)."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

TypeIntervention = Literal["arrosage", "ombrage", "taille", "fertilisation", "traitement", "nettoyage", "diagnostic"]
StatutIntervention = Literal["planifiee", "en_cours", "terminee"]


class InterventionCreate(BaseModel):
    espace_id: int
    type: TypeIntervention
    description: Optional[str] = Field(None, max_length=500)
    volume_eau_l: Optional[float] = Field(None, ge=0)
    planifiee_le: Optional[datetime] = None


class InterventionUpdate(BaseModel):
    type: Optional[TypeIntervention] = None
    description: Optional[str] = Field(None, max_length=500)
    volume_eau_l: Optional[float] = Field(None, ge=0)
    statut: Optional[StatutIntervention] = None
    planifiee_le: Optional[datetime] = None
    realisee_le: Optional[datetime] = None


class InterventionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    espace_id: int
    type: str
    description: Optional[str] = None
    volume_eau_l: Optional[float] = None
    statut: str
    planifiee_le: Optional[datetime] = None
    realisee_le: Optional[datetime] = None
    cree_le: datetime
    cree_par: Optional[int] = None
