from datetime import date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from config import settings

# Ressource prélevée : réseau d'eau potable, forage (nappe), eau de récupération, rivière (cours d'eau)
SourceEau = Literal["reseau", "forage", "recuperation", "riviere"]


class EspaceVertAgronomie(BaseModel):
    """Paramètres agronomiques communs à la création et à la mise à jour."""
    ville: str | None = Field(None, max_length=120)
    zone: str | None = Field(None, max_length=120)
    surface_m2: float | None = Field(None, ge=0)
    type_espace: str | None = Field(None, max_length=50)
    type_sol: str | None = Field(None, max_length=50)
    ph_actuel: float | None = Field(None, ge=0, le=14)
    exposition: str | None = Field(None, max_length=50)
    drainage: str | None = Field(None, max_length=50)
    humidite_cible: float | None = Field(None, ge=0, le=100)
    frequence_arrosage_auto: int | None = Field(None, ge=0)
    profondeur_racinaire: float | None = Field(None, ge=0)  # cm
    type_irrigation: str | None = Field(None, max_length=50)
    debit_arrosage_l_min: float | None = Field(None, gt=0, le=100_000)
    date_derniere_fertilisation: date | None = None
    # Surcharge de la réserve utile (mm) ; absente ou null : calculée (FAO-56, texture × profondeur racinaire)
    reserve_utile_max: float | None = Field(None, gt=0)
    coefficient_cultural: float | None = Field(None, gt=0, le=3)
    # Mode sécheresse : zone d'alerte VigiEau de la ressource, dérogation des jeunes plantations
    source_eau: SourceEau | None = None
    date_plantation: date | None = Field(None, ge=date(1800, 1, 1))


def _plantation_passee(valeur: date | None) -> date | None:
    """Une date de plantation future (2062 pour 2026) priverait l'espace de sa dérogation sans le dire.
    Un jour de marge : fuseau du navigateur."""
    if valeur is not None and valeur > datetime.now(settings.fuseau).date() + timedelta(days=1):
        raise ValueError("la date de plantation ne peut pas être dans le futur")
    return valeur


class EspaceVertCreate(EspaceVertAgronomie):
    """Création : l'organisation et le créateur viennent de la session (jamais fournis par le client)."""
    nom: str = Field(..., min_length=1, max_length=120)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    _date_plantation = field_validator("date_plantation")(_plantation_passee)


class EspaceVertUpdate(EspaceVertAgronomie):
    """Mise à jour partielle : seuls les champs envoyés sont modifiés."""
    nom: str | None = Field(None, min_length=1, max_length=120)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)

    _date_plantation = field_validator("date_plantation")(_plantation_passee)

    @field_validator("source_eau")
    @classmethod
    def _source_renseignee(cls, valeur: str | None) -> str:
        if valeur is None:
            raise ValueError("la source d'eau ne peut pas être vide (reseau par défaut)")
        return valeur


class EspaceVertRead(EspaceVertAgronomie):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    latitude: float
    longitude: float
    organisation_id: int
    cree_par: int | None = None
    zone_id: int | None = None
    sante_percent: float | None = None
    cree_le: datetime | None = None
    # Réserve utilisée par le bilan : reserve_utile_max si saisie, sinon la TAW calculée
    reserve_utile_effective_mm: float
    source_eau: str = "reseau"
