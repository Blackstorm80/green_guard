from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Schéma de réponse pour l'utilisateur connecté
class User(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool = True
    
    class Config:
        from_attributes = True  # Pour SQLAlchemy -> Pydantic v2

# Schéma pour la création d'utilisateur (via script ou futur endpoint)
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
