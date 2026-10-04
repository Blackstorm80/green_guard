from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from api.deps.auth import exiger_role, get_current_user
from domain import models
from domain.logic.droits import ROLES_GESTION
from infrastructure.database import get_db
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from schema.espaces_verts import EspaceVertCreate, EspaceVertRead, EspaceVertUpdate

router = APIRouter()
gestionnaire = exiger_role(*ROLES_GESTION)


def _espace_de_l_organisation(espace_id: int, db: Session, user: models.User) -> models.EspaceVert:
    """404 aussi bien pour un espace inexistant que pour celui d'une autre organisation (pas de fuite d'existence)."""
    espace = EspaceVertRepositoryImpl(db).get_pour_organisation(espace_id, user.organisation_id)
    if espace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Espace vert introuvable")
    return espace


@router.get("/", response_model=list[EspaceVertRead])
def get_espaces_verts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Patrimoine de l'organisation de l'utilisateur connecté."""
    return EspaceVertRepositoryImpl(db).list_par_organisation(current_user.organisation_id)


@router.post("/", response_model=EspaceVertRead, status_code=status.HTTP_201_CREATED)
def create_espace_vert(
    espace_data: EspaceVertCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(gestionnaire),
):
    """Crée un espace vert dans l'organisation de l'utilisateur connecté."""
    espace = models.EspaceVert(**espace_data.model_dump(exclude_none=True),
                               organisation_id=current_user.organisation_id, cree_par=current_user.id)
    return EspaceVertRepositoryImpl(db).save(espace)


@router.get("/{espace_id}", response_model=EspaceVertRead)
def get_espace_vert(
    espace_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return _espace_de_l_organisation(espace_id, db, current_user)


@router.put("/{espace_id}", response_model=EspaceVertRead)
def update_espace_vert(
    espace_id: int,
    espace_data: EspaceVertUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(gestionnaire),
):
    """Mise à jour partielle : seuls les champs envoyés sont modifiés."""
    espace = _espace_de_l_organisation(espace_id, db, current_user)
    for key, value in espace_data.model_dump(exclude_unset=True).items():
        setattr(espace, key, value)
    return EspaceVertRepositoryImpl(db).save(espace)


@router.delete("/{espace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_espace_vert(
    espace_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(gestionnaire)
):
    espace = _espace_de_l_organisation(espace_id, db, current_user)
    db.delete(espace)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
