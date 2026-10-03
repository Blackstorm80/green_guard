from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

LONGUEUR_MIN_MOT_DE_PASSE = 12


class User(BaseModel):
    """Profil renvoyé à l'utilisateur connecté (jamais le hash)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    is_active: bool = True
    avatar_url: Optional[str] = None


class UserCreate(BaseModel):
    """Inscription : le rôle est assigné par le backend uniquement."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=LONGUEUR_MIN_MOT_DE_PASSE, max_length=128)
