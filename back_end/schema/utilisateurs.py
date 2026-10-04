from pydantic import BaseModel, ConfigDict, EmailStr, Field

LONGUEUR_MIN_MOT_DE_PASSE = 12


class OrganisationResume(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str


class User(BaseModel):
    """Profil renvoyé à l'utilisateur connecté (jamais le hash)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    permissions: list[str] = []
    est_superadmin: bool = False
    organisation: OrganisationResume
    is_active: bool = True
    avatar_url: str | None = None


class UserCreate(BaseModel):
    """Inscription : le rôle est assigné par le backend uniquement (admin de la nouvelle organisation)."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=LONGUEUR_MIN_MOT_DE_PASSE, max_length=128)
    organisation: str | None = Field(None, min_length=1, max_length=120,
                                     description="Nom de la collectivité ; par défaut « Organisation de <nom> ».")
