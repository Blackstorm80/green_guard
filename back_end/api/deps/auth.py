import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from domain.models import User
from infrastructure.database import get_db

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Variable d'environnement SECRET_KEY manquante")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


#  SECTION 1 : MOTS DE PASSE (bcrypt)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# SECTION 2 : JETONS (JWT)
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    maintenant = datetime.now(timezone.utc)
    to_encode = data.copy()
    to_encode.update({
        "iat": maintenant,
        "exp": maintenant + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)),
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


#  SECTION 3 : UTILISATEUR COURANT
async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session invalide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
    except JWTError:
        raise credentials_exception
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    # Un compte désactivé perd immédiatement l'accès, même avec un jeton encore valide
    if user is None or not user.is_active:
        raise credentials_exception
    return user


# Alias conservé pour les routes existantes : get_current_user vérifie déjà is_active
get_current_active_user = get_current_user


#  SECTION 4 : RÔLES (lus en base, jamais depuis le jeton)
def require_role(role: str):
    return require_any_role([role])


def require_any_role(roles: List[str]):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")
        return current_user
    return role_checker
