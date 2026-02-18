from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from infrastructure.database import get_db_session
from api.deps.auth import verify_password, create_access_token
from domain.entities.user import UserEntity
from schemas.token import Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
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
    db=Depends(get_db_session)
):
    """Inscription temporaire"""
    return {"message": f"Utilisateur {name} créé", "email": email}