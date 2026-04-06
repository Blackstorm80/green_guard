from pydantic import BaseModel, EmailStr
from typing import Optional

# Schéma de base pour les propriétés partagées
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: Optional[str] = "user"

# Schéma pour la création d'un utilisateur (ex: via un endpoint admin)
class UserCreate(UserBase):
    password: str

# Schéma pour la lecture/retour d'un utilisateur depuis l'API
# C'est le modèle qui sera utilisé pour le endpoint /me
class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True