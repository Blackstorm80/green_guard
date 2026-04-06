from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict 


# Schéma de réponse pour l'utilisateur connecté
class User(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool = True
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True  # Pour SQLAlchemy -> Pydantic v2

# Schéma pour la création d'utilisateur (via endpoint)
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"

# Schéma pour mise à jour
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

# Token JWT
class Token(BaseModel):
    access_token: str
    token_type: str

# Données extraites du token
class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class EspaceVertBase(BaseModel):
    nom: str
    ville: Optional[str] = None
    latitude: float
    longitude: float
    surface_m2: Optional[float] = None
    user_id: int

class EspaceVertCreate(EspaceVertBase):
    pass


#  ZoneIntelligente (Zone) Schema

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

#  Capteur (Sensor) Schemas 

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

#  Schéma pour le diagnostic santé 
  
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
