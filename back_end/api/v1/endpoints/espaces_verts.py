from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from infrastructure.database import get_db
from api.deps.auth import get_current_user
from domain import models # On importe le module domain/models en entier
from schema.espaces_verts import EspaceVertRead, EspaceVertCreate, EspaceVertUpdate

router = APIRouter()

@router.post("/", response_model=EspaceVertRead)
def create_espace_vert(
    espace_data: EspaceVertCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Crée un nouvel espace vert pour l'utilisateur connecté.
    """
    # Assure que le nouvel espace est bien lié à l'utilisateur qui le crée
    if espace_data.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez créer des espaces que pour vous-même.")

    db_espace = models.EspaceVert(**espace_data.model_dump())
    db.add(db_espace)
    db.commit()
    db.refresh(db_espace)
    return db_espace

@router.get("/", response_model=List[EspaceVertRead])
def get_espaces_verts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Récupère uniquement les espaces verts appartenant à l'utilisateur connecté.
    """
    return db.query(models.EspaceVert).filter(models.EspaceVert.user_id == current_user.id).all()

@router.put("/{espace_id}", response_model=EspaceVertRead)
def update_espace_vert(
    espace_id: int,
    espace_data: EspaceVertUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Met à jour les données (notamment agronomiques) d'un espace vert.
    """
    db_espace = db.query(models.EspaceVert).filter(models.EspaceVert.id == espace_id).first()

    if not db_espace:
        raise HTTPException(status_code=404, detail="Espace vert non trouvé")

    # Vérifier que Nathan ne peut modifier que ses propres espaces
    if db_espace.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à modifier cet espace")

    update_data = espace_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_espace, key, value)

    db.add(db_espace)
    db.commit()
    db.refresh(db_espace)
    return db_espace