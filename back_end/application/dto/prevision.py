from datetime import date

from pydantic import BaseModel, ConfigDict

from application.dto.capteurs import DecisionDTO


class JourPrevisionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    jour: date
    reserve_mm: float
    reserve_percent: float | None = None
    statut: str
    et0_mm: float | None = None
    pluie_mm: float
    probabilite_pluie_pct: float | None = None
    # Pluie retenue par la règle prudente (acquise seulement à J+1 et J+2, pondérée par la probabilité au-delà)
    pluie_comptee_mm: float
    pluie_acquise: bool
    indicatif: bool        # au-delà de J+3 : hors horizon de décision
    issu_du_bilan: bool    # J repris du bilan du jour


class PrevisionDTO(BaseModel):
    espace_id: int
    date_calcul: date
    date_bilan: date
    reserve_max_mm: float
    jours: list[JourPrevisionDTO]
    date_bascule_a_surveiller: date | None = None
    date_bascule_critique: date | None = None
    decision: DecisionDTO
    avertissement: str
    source_meteo: str | None = None
