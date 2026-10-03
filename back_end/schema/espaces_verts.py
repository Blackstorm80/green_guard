from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


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
    profondeur_racinaire: float | None = Field(None, ge=0)
    type_irrigation: str | None = Field(None, max_length=50)
    date_derniere_fertilisation: date | None = None
    reserve_utile_max: float | None = Field(None, gt=0)
    coefficient_cultural: float | None = Field(None, gt=0, le=3)


class EspaceVertCreate(EspaceVertAgronomie):
    """Création : le propriétaire est toujours l'utilisateur authentifié (jamais fourni par le client)."""
    nom: str = Field(..., min_length=1, max_length=120)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class EspaceVertUpdate(EspaceVertAgronomie):
    """Mise à jour partielle : seuls les champs envoyés sont modifiés."""
    nom: str | None = Field(None, min_length=1, max_length=120)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)


class EspaceVertRead(EspaceVertAgronomie):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    latitude: float
    longitude: float
    user_id: int
    zone_id: int | None = None
    sante_percent: float | None = None
    cree_le: datetime | None = None
