from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EspaceVertAgronomie(BaseModel):
    """Paramètres agronomiques communs à la création et à la mise à jour."""
    ville: Optional[str] = Field(None, max_length=120)
    zone: Optional[str] = Field(None, max_length=120)
    surface_m2: Optional[float] = Field(None, ge=0)
    type_espace: Optional[str] = Field(None, max_length=50)
    type_sol: Optional[str] = Field(None, max_length=50)
    ph_actuel: Optional[float] = Field(None, ge=0, le=14)
    exposition: Optional[str] = Field(None, max_length=50)
    drainage: Optional[str] = Field(None, max_length=50)
    humidite_cible: Optional[float] = Field(None, ge=0, le=100)
    frequence_arrosage_auto: Optional[int] = Field(None, ge=0)
    profondeur_racinaire: Optional[float] = Field(None, ge=0)
    type_irrigation: Optional[str] = Field(None, max_length=50)
    date_derniere_fertilisation: Optional[date] = None
    reserve_utile_max: Optional[float] = Field(None, gt=0)
    coefficient_cultural: Optional[float] = Field(None, gt=0, le=3)


class EspaceVertCreate(EspaceVertAgronomie):
    """Création : le propriétaire est toujours l'utilisateur authentifié (jamais fourni par le client)."""
    nom: str = Field(..., min_length=1, max_length=120)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class EspaceVertUpdate(EspaceVertAgronomie):
    """Mise à jour partielle : seuls les champs envoyés sont modifiés."""
    nom: Optional[str] = Field(None, min_length=1, max_length=120)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class EspaceVertRead(EspaceVertAgronomie):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    latitude: float
    longitude: float
    user_id: int
    zone_id: Optional[int] = None
    sante_percent: Optional[float] = None
    cree_le: Optional[datetime] = None
