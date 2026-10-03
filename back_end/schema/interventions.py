"""Schémas des interventions terrain (repris du travail de la branche feature/Lucresse-branche)."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TypeIntervention = Literal["arrosage", "ombrage", "taille", "fertilisation", "traitement", "nettoyage", "diagnostic"]
StatutIntervention = Literal["planifiee", "en_cours", "terminee"]


class InterventionCreate(BaseModel):
    espace_id: int
    type: TypeIntervention
    description: str | None = Field(None, max_length=500)
    volume_eau_l: float | None = Field(None, ge=0)
    planifiee_le: datetime | None = None


class InterventionUpdate(BaseModel):
    type: TypeIntervention | None = None
    description: str | None = Field(None, max_length=500)
    volume_eau_l: float | None = Field(None, ge=0)
    statut: StatutIntervention | None = None
    planifiee_le: datetime | None = None
    realisee_le: datetime | None = None


class InterventionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    espace_id: int
    type: str
    description: str | None = None
    volume_eau_l: float | None = None
    statut: str
    planifiee_le: datetime | None = None
    realisee_le: datetime | None = None
    cree_le: datetime
    cree_par: int | None = None
