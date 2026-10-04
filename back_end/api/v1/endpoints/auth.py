from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.deps.auth import (
    create_access_token,
    effacer_cookie_session,
    get_password_hash,
    poser_cookie_session,
    verify_password,
)
from api.deps.rate_limit import LimiteurConnexion, RateLimiter
from application.use_cases.organisations import EmailDejaUtiliseError, inscrire
from config import settings
from domain.models import User
from infrastructure.database import get_db
from infrastructure.repositories.organisation_repository_impl import OrganisationRepositoryImpl
from infrastructure.rls import contournement_rls
from schema.token import Token
from schema.utilisateurs import UserCreate

router = APIRouter()
limiteur_connexion = LimiteurConnexion(
    max_par_ip=settings.auth_rate_limit_ip,
    max_par_identifiant=settings.auth_rate_limit,
    fenetre_s=settings.auth_rate_window_s,
)
limiteur_inscription = RateLimiter(settings.auth_rate_limit, settings.auth_rate_window_s)


@router.post("/login", response_model=Token, dependencies=[Depends(limiteur_connexion)])
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Ouvre une session : cookie httpOnly pour le navigateur ; jeton aussi renvoyé pour Swagger et les scripts."""
    with contournement_rls(db):  # compte cherché avant de connaître son organisation
        user = db.query(User).filter(User.email == form_data.username).first()
    # Même réponse pour « compte inconnu », « mauvais mot de passe » et « compte désactivé »
    if not user or not verify_password(form_data.password, user.hashed_password) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expiration = create_access_token(user.email)
    poser_cookie_session(response, token, expiration)
    return {"access_token": token, "token_type": "bearer", "expires_at": expiration}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    """Ferme la session navigateur (supprime le cookie)."""
    effacer_cookie_session(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/register", status_code=status.HTTP_201_CREATED, dependencies=[Depends(limiteur_inscription)])
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Crée un compte et sa propre organisation, dont il est administrateur (le rôle n'est jamais
    fourni par le client). Provisoire : rejoindre une organisation existante passera par une invitation."""
    refus = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossible de créer ce compte.")
    # Création d'une organisation et unicité de l'e-mail : opérations à l'échelle de l'instance
    with contournement_rls(db):
        try:
            inscrire(OrganisationRepositoryImpl(db), name=user_in.name, email=user_in.email,
                     mot_de_passe_hache=get_password_hash(user_in.password), nom_organisation=user_in.organisation)
        except (EmailDejaUtiliseError, IntegrityError):
            db.rollback()
            raise refus from None
    return {"message": "Compte créé avec succès."}
