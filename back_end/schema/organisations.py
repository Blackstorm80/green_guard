import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from schema.utilisateurs import LONGUEUR_MIN_MOT_DE_PASSE

RoleMembre = Literal["admin", "gestionnaire", "technicien", "lecteur"]
TAILLE_MAX_PARAMETRES = 10_000  # caractères, une fois sérialisés en JSON
MOTIF_SLUG = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class OrganisationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    slug: str
    parametres: dict[str, Any] | None = None
    cree_le: datetime | None = None


class OrganisationUpdate(BaseModel):
    """Le nom est réservé à l'administrateur ; les paramètres métier au gestionnaire et à l'administrateur."""
    nom: str | None = Field(None, min_length=1, max_length=120)
    parametres: dict[str, Any] | None = None

    @field_validator("parametres")
    @classmethod
    def _taille_bornee(cls, valeur: dict | None) -> dict | None:
        if valeur is not None and len(json.dumps(valeur)) > TAILLE_MAX_PARAMETRES:
            raise ValueError(f"paramètres trop volumineux (maximum {TAILLE_MAX_PARAMETRES} caractères)")
        return valeur


class AdminInitial(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=LONGUEUR_MIN_MOT_DE_PASSE, max_length=128)


class OrganisationCreate(BaseModel):
    nom: str = Field(..., min_length=1, max_length=120)
    slug: str | None = Field(None, min_length=1, max_length=60, pattern=MOTIF_SLUG)
    admin: AdminInitial


class MembreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    is_active: bool


class MembreUpdate(BaseModel):
    role: RoleMembre | None = None
    is_active: bool | None = None
