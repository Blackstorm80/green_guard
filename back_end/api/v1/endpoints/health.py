from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.deps.auth import get_current_user
from api.v1.endpoints.capteurs import get_capteur_service
from application.dto.capteurs import DiagnosticDTO
from application.use_cases.bilans_hydriques import diagnostiquer_espace
from application.use_cases.secheresse import evaluer_espace, restrictions_en_vigueur
from config import settings
from domain.logic.secheresse import regles_depuis_parametres
from domain.models import User
from infrastructure.database import get_db
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.repositories.restriction_secheresse_repository_impl import RestrictionSecheresseRepositoryImpl
from infrastructure.services.capteur_hybrid_service import CapteurHybridService

router = APIRouter()


class DiagnosticRequest(BaseModel):
    espace_id: int


@router.get("/live", tags=["Supervision"])
def liveness():
    """Sonde de vie (aucune dépendance)."""
    return {"status": "ok"}


@router.get("/ready", tags=["Supervision"])
def readiness(db: Session = Depends(get_db)):
    """Sonde de disponibilité : vérifie l'accès à la base."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Base de données indisponible"
        ) from None
    return {"status": "ok"}


@router.post("/diagnostic", response_model=DiagnosticDTO)
def run_diagnostic(
    payload: DiagnosticRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    capteurs: CapteurHybridService = Depends(get_capteur_service),
):
    """Diagnostic d'un espace de l'organisation à partir de ses dernières mesures réelles (lecture seule)."""
    espace = EspaceVertRepositoryImpl(db).get_pour_organisation(payload.espace_id, current_user.organisation_id)
    if espace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Espace vert introuvable")
    aujourd_hui = datetime.now(settings.fuseau).date()
    restriction = restrictions_en_vigueur([espace.id], aujourd_hui, RestrictionSecheresseRepositoryImpl(db))
    evaluation = evaluer_espace(espace, restriction.get(espace.id),
                                regles_depuis_parametres(current_user.organisation.parametres), aujourd_hui)
    return diagnostiquer_espace(espace, capteurs, BilanHydriqueRepositoryImpl(db), evaluation)
