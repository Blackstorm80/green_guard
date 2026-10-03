from datetime import datetime

from pydantic import BaseModel


class Token(BaseModel):
    """Réponse de connexion. Le navigateur utilise le cookie httpOnly ; le jeton sert à Swagger et aux scripts."""
    access_token: str
    token_type: str
    expires_at: datetime
