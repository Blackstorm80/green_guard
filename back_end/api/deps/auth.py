"""Authentification : mots de passe bcrypt, jetons JWT (PyJWT), session par cookie httpOnly.

Le jeton est accepté depuis le cookie de session (navigateur) ou l'en-tête
Authorization: Bearer (Swagger, scripts, tests). Pour une requête authentifiée par
cookie qui modifie des données, l'en-tête X-Requested-With est exigé : un site tiers
ne peut pas l'ajouter sans passer le contrôle CORS, ce qui bloque le CSRF.
"""
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from config import settings
from domain.models import User
from infrastructure.database import get_db

ALGORITHM = "HS256"
EN_TETE_CSRF = "X-Requested-With"
METHODES_SURES = {"GET", "HEAD", "OPTIONS"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


#  SECTION 1 : MOTS DE PASSE (bcrypt)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# SECTION 2 : JETONS (JWT)
def create_access_token(subject: str, expires_delta: timedelta | None = None) -> tuple[str, datetime]:
    maintenant = datetime.now(UTC)
    expiration = maintenant + (expires_delta or timedelta(minutes=settings.access_token_minutes))
    payload = {"sub": subject, "iat": maintenant, "exp": expiration, "jti": uuid.uuid4().hex, "type": "access"}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM), expiration


def poser_cookie_session(response: Response, token: str, expiration: datetime) -> None:
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        expires=expiration,
        httponly=True,                 # illisible par JavaScript : protège du vol par XSS
        secure=settings.cookie_secure,
        samesite="lax",
        path="/api",
    )


def effacer_cookie_session(response: Response) -> None:
    response.delete_cookie(key=settings.cookie_name, path="/api", httponly=True,
                           secure=settings.cookie_secure, samesite="lax")


#  SECTION 3 : UTILISATEUR COURANT
# Synchrone volontairement : elle interroge la base. En `async def`, elle s'exécuterait sur la
# boucle d'événements et la bloquerait en attendant une connexion du pool (interblocage sous charge).
def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    bearer: str | None = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session invalide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = bearer
    via_cookie = False
    if not token:
        token = request.cookies.get(settings.cookie_name)
        via_cookie = token is not None
    if not token:
        raise credentials_exception

    if via_cookie and request.method not in METHODES_SURES and not request.headers.get(EN_TETE_CSRF):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requête refusée (protection CSRF)")

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM],
                             options={"require": ["exp", "sub"]})
    except jwt.PyJWTError:
        raise credentials_exception from None
    if payload.get("type") != "access":
        raise credentials_exception

    user = db.query(User).filter(User.email == payload["sub"]).first()
    # Un compte désactivé perd immédiatement l'accès, même avec un jeton encore valide
    if user is None or not user.is_active:
        raise credentials_exception
    return user


# Alias conservé pour les routes existantes : get_current_user vérifie déjà is_active
get_current_active_user = get_current_user


#  SECTION 4 : RÔLES (lus en base, jamais depuis le jeton)
def require_role(role: str):
    return require_any_role([role])


def require_any_role(roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")
        return current_user
    return role_checker
