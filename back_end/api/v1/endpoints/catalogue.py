from typing import List, Optional

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
    nom_scientifique: Optional[str] = None
    nom_commun: Optional[str] = None
    famille: Optional[str] = None
    ph_ideal: Optional[float] = None
    besoin_eau: Optional[str] = None
    url_image: Optional[str] = None


class AuxiliaireRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    url_image: Optional[str] = None


@router.get("/plantes", response_model=List[PlanteRead])
def get_plantes(
    offset: int = Query(0, ge=0),
    limit: int = Query(LIMITE_MAX, ge=1, le=LIMITE_MAX),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Plante).order_by(Plante.nom_commun).offset(offset).limit(limit).all()


@router.get("/auxiliaires", response_model=List[AuxiliaireRead])
def get_auxiliaires(
    offset: int = Query(0, ge=0),
    limit: int = Query(LIMITE_MAX, ge=1, le=LIMITE_MAX),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Auxiliaire).order_by(Auxiliaire.nom).offset(offset).limit(limit).all()
