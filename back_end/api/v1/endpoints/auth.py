from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from infrastructure.database import get_db_session
from application.dto.user import UserDTO
from api.deps.auth import get_current_user, verify_password
from domain.entities.user import UserEntity

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(
    username: str,
    password: str,
    db: Session = Depends(get_db_session)
):
    """Login pour obtenir un token d'accès."""
    user = db.query(UserEntity).filter(UserEntity.email == username).first()

    # Vérifie si l'utilisateur existe ET si le mot de passe est correct
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # À ce stade, l'authen est faite.
    # Ici, je cree et retourne un vrai token JWT.
    # Pour l'instant, je retourne le token factice , je recherche encore sur comment creer un vrai tken .
    return {"access_token": "fake-token-admin", "token_type": "bearer"}

@router.post("/register")
async def register(
    email: str,
    name: str,
    db=Depends(get_db_session)
):
    """Inscription temporaire"""
    return {"message": f"Utilisateur {name} créé", "email": email}