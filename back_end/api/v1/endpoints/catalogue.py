from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from api.deps.auth import get_current_user
from domain.models import Auxiliaire, Plante, User
from infrastructure.database import get_db

router = APIRouter()
LIMITE_MAX = 2000


class PlanteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom_scientifique: str | None = None
    nom_commun: str | None = None
    famille: str | None = None
    ph_ideal: float | None = None
    besoin_eau: str | None = None
    url_image: str | None = None


class AuxiliaireRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str | None = None
    description: str | None = None
    role: str | None = None
    url_image: str | None = None


@router.get("/plantes", response_model=list[PlanteRead])
def get_plantes(
    offset: int = Query(0, ge=0),
    limit: int = Query(LIMITE_MAX, ge=1, le=LIMITE_MAX),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Plante).order_by(Plante.nom_commun).offset(offset).limit(limit).all()


@router.get("/auxiliaires", response_model=list[AuxiliaireRead])
def get_auxiliaires(
    offset: int = Query(0, ge=0),
    limit: int = Query(LIMITE_MAX, ge=1, le=LIMITE_MAX),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Auxiliaire).order_by(Auxiliaire.nom).offset(offset).limit(limit).all()
