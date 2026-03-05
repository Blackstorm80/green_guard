# back_end/schema/schemas.py

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# ================== User Schemas ==================

class UserBase(BaseModel):
    name: str
    email: str
    role: str = "user"

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ================== EspaceVert (Space) Schemas ==================

class EspaceVertBase(BaseModel):
    nom: str
    ville: Optional[str] = None
    latitude: float
    longitude: float
    surface_m2: Optional[float] = None
    user_id: int

class EspaceVertCreate(EspaceVertBase):
    pass

class EspaceVertRead(EspaceVertBase):
    id: int
    sante_percent: float
    model_config = ConfigDict(from_attributes=True)

# ================== ZoneIntelligente (Zone) Schemas ==================

class ZoneIntelligenteBase(BaseModel):
    nom: str
    user_id: int
    config_id: Optional[int] = None

class ZoneIntelligenteCreate(ZoneIntelligenteBase):
    pass

class ZoneIntelligenteRead(ZoneIntelligenteBase):
    id: int
    centroid_lat: float
    centroid_lon: float
    rayon_km: float
    sante_moyenne: float
    nb_espaces: int
    model_config = ConfigDict(from_attributes=True)

# ================== Capteur (Sensor) Schemas ==================

class CapteurBase(BaseModel):
    nom: str
    type: str  # Utiliser str pour la simplicité, pourrait être un Enum
    emplacement: Optional[str] = None
    espace_id: int

class CapteurCreate(CapteurBase):
    pass

class CapteurRead(CapteurBase):
    id: int
    est_actif: bool
    cree_le: datetime
    model_config = ConfigDict(from_attributes=True)

# ================== Schéma pour le diagnostic santé ==================

class MesuresIOT(BaseModel):
    temperature: float
    humidite_rel: float
    humidite_sol: float
    co2: float

class HealthDiagnosticRequest(BaseModel):
    espace_id: int
    mesures: MesuresIOT

class HealthDiagnosticResponse(BaseModel):
    espace_id: int
    nom: str
    score_global: float
    stresses: dict
    recommandations: list
    alertes_generees: int # On retourne juste le nombre, pas les objets
