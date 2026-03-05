from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from api.deps.auth import verify_password, create_access_token
from domain.models import User
from schema.token import Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login pour obtenir un token d'accès."""
    # OAuth2PasswordRequestForm nous donne 'username' et 'password'
    user = db.query(User).filter(User.email == form_data.username).first()

    # Vérifie si l'utilisateur existe ET si le mot de passe est correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # L'authentification est réussie, on crée le token JWT
    # en y incluant le rôle de l'utilisateur.
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
async def register(
    email: str,
    name: str,
    db=Depends(get_db)
):
    """Inscription temporaire"""
    return {"message": f"Utilisateur {name} créé", "email": email}