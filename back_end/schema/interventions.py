"""Schémas des interventions terrain (repris du travail de la branche feature/Lucresse-branche)."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TypeIntervention = Literal["arrosage", "ombrage", "taille", "fertilisation", "traitement", "nettoyage", "diagnostic"]
StatutIntervention = Literal["planifiee", "en_cours", "terminee"]
# 10 000 m³ : borne de saisie (une tonne à eau contient 5 à 15 m³)
VOLUME_MAX_L = 10_000_000


class InterventionCreate(BaseModel):
    """Un arrosage créé directement terminé avec un volume est aussitôt compté dans le bilan."""
    espace_id: int
    type: TypeIntervention
    description: str | None = Field(None, max_length=500)
    volume_eau_l: float | None = Field(None, ge=0, le=VOLUME_MAX_L)
    statut: StatutIntervention = "planifiee"
    planifiee_le: datetime | None = None
    realisee_le: datetime | None = None


class InterventionUpdate(BaseModel):
    type: TypeIntervention | None = None
    description: str | None = Field(None, max_length=500)
    volume_eau_l: float | None = Field(None, ge=0, le=VOLUME_MAX_L)
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
    # Hauteur d'eau comptée dans le bilan (volume / surface) ; None si l'intervention n'apporte rien
    arrosage_compte_mm: float | None = None
    # Registre sécheresse d'un arrosage réalisé (niveau VigiEau, plage interdite, dérogation, zone, agent)
    realisee_par: int | None = None
    secheresse_niveau: str | None = None
    secheresse_plage_interdite: str | None = None
    secheresse_derogation: str | None = None
    secheresse_zone: str | None = None
    avertissement_secheresse: str | None = None
