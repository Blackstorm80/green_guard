from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from application.dto.user import UserDTO

# Configuration pour le hachage des mots de passe (bcrypt est un standard robuste)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe en clair contre un mot de passe haché."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashe un mot de passe."""
    return pwd_context.hash(password)

def fake_decode_token(token: str) -> Optional[UserDTO]:
    """
    TEMPORAIRE : décode le token et renvoie un utilisateur.
    À remplacer par un vrai décodage JWT plus tard.
    """
    if token == "fake-token-admin":
        return UserDTO(id=1, name="Admin Demo", email="admin@demo.com", role="admin")
    return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserDTO:
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou utilisateur inconnu",
        )
    return user