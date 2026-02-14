# back_end/api/deps/auth.py
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from application.dto.user import UserDTO

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def fake_decode_token(token: str) -> Optional[UserDTO]:
    """
    TEMPORAIRE : decode le token et renvoie un user.
    À remplacer par un vrai décodage JWT plus tard.
    """
    if token == "fake-token-admin":
        return UserDTO(id=1, name="Admin Vert", email="admin@example.com", role="admin")
    if token == "fake-token-user":
        return UserDTO(id=2, name="Utilisateur Demo", email="user@example.com", role="manager")
    return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserDTO:
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou utilisateur inconnu",
        )
    return user