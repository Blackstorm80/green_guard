"""Règles du mode sécheresse d'une organisation (organisations.parametres["secheresse"]).

Chaque niveau doit être décrit explicitement (interdit et plage) : une règle incomplète ne doit jamais
lever une interdiction sans que l'administrateur l'ait voulu. Une dérogation omise prend la valeur
par défaut du guide national (plage interdite des jeunes plantations comprise).
"""
from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.logic.secheresse import JEUNES_PLANTATIONS_ANS_MAX

MOTIF_HEURE = r"^([01]\d|2[0-3]):[0-5]\d$"


class PlageHoraireSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    debut: str = Field(..., pattern=MOTIF_HEURE, examples=["11:00"])
    fin: str = Field(..., pattern=MOTIF_HEURE, examples=["18:00"])

    @model_validator(mode="after")
    def _ordonnee(self):
        if self.debut >= self.fin:
            raise ValueError("la plage doit commencer avant de finir, dans la même journée")
        return self


def _plage_guide() -> PlageHoraireSchema:
    return PlageHoraireSchema(debut="11:00", fin="18:00")


class RegleNiveauSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interdit: bool = Field(..., description="Interdit toute la journée")
    plage_interdite: PlageHoraireSchema | None = Field(
        ..., description="Sinon, plage interdite (null : arrosage autorisé toute la journée)")


class NiveauxSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vigilance: RegleNiveauSchema
    alerte: RegleNiveauSchema
    alerte_renforcee: RegleNiveauSchema
    crise: RegleNiveauSchema


class DerogationsSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Âge (ans) en deçà duquel une plantation peut être arrosée ; null ou 0 : dérogation désactivée
    jeunes_plantations_ans: float | None = Field(2, ge=0, le=JEUNES_PLANTATIONS_ANS_MAX)
    # Plage qui reste interdite aux jeunes plantations ; null explicite : aucune plage
    plage_interdite_jeunes_plantations: PlageHoraireSchema | None = Field(default_factory=_plage_guide)
    eau_recuperation: bool = True


class ReglesSecheresseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    niveaux: NiveauxSchema
    derogations: DerogationsSchema = Field(default_factory=DerogationsSchema)


class ReglesSecheresseRead(ReglesSecheresseSchema):
    model_config = ConfigDict(extra="ignore")

    personnalisees: bool     # false : règles par défaut (guide national 2023)
    source: str
