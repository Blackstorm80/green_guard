from fastapi import APIRouter, Depends, HTTPException, status
from infrastructure.database import get_db_session
from application.dto.user import UserDTO
from api.deps.auth import get_current_user  # ← Importe tes dépendances

router = APIRouter(prefix="/auth", tags=["auth"])  # ← ÇA C'EST IMPORTANT


@router.post("/login")
async def login(
    username: str,
    password: str,
    db=Depends(get_db_session)
):
    """Login temporaire - à remplacer par JWT réel"""
    if username == "admin" and password == "admin":
        return {"access_token": "fake-token-admin", "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Identifiants incorrects")

@router.post("/register")
async def register(
    email: str,
    name: str,
    db=Depends(get_db_session)
):
    """Inscription temporaire"""
    return {"message": f"Utilisateur {name} créé", "email": email}