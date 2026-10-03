from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.deps.auth import create_access_token, get_password_hash, verify_password
from domain.models import User
from infrastructure.database import get_db
from schema.token import Token
from schema.utilisateurs import UserCreate

router = APIRouter()


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Échange email + mot de passe contre un jeton d'accès."""
    user = db.query(User).filter(User.email == form_data.username).first()
    # Même réponse pour « compte inconnu », « mauvais mot de passe » et « compte désactivé »
    if not user or not verify_password(form_data.password, user.hashed_password) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(data={"sub": user.email}), "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Crée un compte. Le rôle est toujours « user » : jamais fourni par le client."""
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossible de créer ce compte.")

    new_user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role="user",
    )
    db.add(new_user)
    db.commit()
    return {"message": "Compte créé avec succès."}
