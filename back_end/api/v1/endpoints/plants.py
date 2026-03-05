from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from infrastructure.database import get_db
from domain.models import EspaceVert, User
from api.deps.auth import require_any_role

router = APIRouter()

# --- Schemas Pydantic (Définis ici pour l'instant) ---

class EspaceVertBase(BaseModel):
    nom: str
    type_espace: str | None = None
    ville: str | None = None
    surface_m2: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    type_sol: str | None = None
    reserve_utile_max: float | None = None
    coefficient_cultural: float | None = None

class EspaceVertCreate(EspaceVertBase):
    pass

class EspaceVertRead(EspaceVertBase):
    id: int
    user_id: int | None = None

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/", response_model=List[EspaceVertRead], summary="Lister les espaces verts")
def read_plants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role(["admin", "user"]))
):
    """
    Récupère la liste de tous les espaces verts enregistrés.
    """
    plants = db.query(EspaceVert).offset(skip).limit(limit).all()
    return plants

@router.post("/", response_model=EspaceVertRead, status_code=status.HTTP_201_CREATED, summary="Créer un espace vert")
def create_plant(
    plant: EspaceVertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role(["admin", "user"]))
):
    """
    Crée un nouvel espace vert.
    """
    db_plant = EspaceVert(
        nom=plant.nom,
        type_espace=plant.type_espace,
        ville=plant.ville,
        superficie_m2=plant.surface_m2,
        latitude=plant.latitude,
        longitude=plant.longitude,
        type_sol=plant.type_sol,
        reserve_utile_max=plant.reserve_utile_max,
        coefficient_cultural=plant.coefficient_cultural,
        user_id=current_user.id
    )
    db.add(db_plant)
    db.commit()
    db.refresh(db_plant)
    return db_plant