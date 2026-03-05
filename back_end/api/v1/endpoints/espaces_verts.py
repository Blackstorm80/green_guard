# back_end/api/v1/endpoints/espaces_verts.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from infrastructure.database import get_db
from infrastructure.repositories.base_repository import BaseRepository
from domain.models import EspaceVert
from schema.schemas import EspaceVertCreate, EspaceVertRead

router = APIRouter()

@router.post("/", response_model=EspaceVertRead)
def create_espace_vert(
    *,
    db: Session = Depends(get_db),
    espace_vert_in: EspaceVertCreate
):
    """
    Crée un nouvel espace vert.
    """
    espace_vert_repo = BaseRepository(db, EspaceVert)
    return espace_vert_repo.create(obj_in=espace_vert_in)

@router.get("/", response_model=List[EspaceVertRead])
def read_espaces_verts(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Récupère une liste d'espaces verts.
    """
    espace_vert_repo = BaseRepository(db, EspaceVert)
    return espace_vert_repo.get_all(skip=skip, limit=limit)
