from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.deps.auth import get_current_user
from api.v1.endpoints.capteurs import get_capteur_service
from application.dto.capteurs import LectureCapteurDTO
from domain.models import User
from domain.ports.capteurs import STATUT_SANS_DONNEE
from infrastructure.database import get_db
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.services.capteur_hybrid_service import CapteurHybridService

router = APIRouter()

MESSAGES = {
    "Optimal": "L'espace vert est dans des conditions optimales.",
    "A surveiller": "Réserve en eau en baisse : un arrosage est à prévoir.",
    "Critique": "Stress hydrique critique : arrosage recommandé sans délai.",
    STATUT_SANS_DONNEE: "Aucune mesure disponible pour cet espace pour le moment.",
}


class DiagnosticRequest(BaseModel):
    espace_id: int


class DiagnosticResponse(BaseModel):
    statut: str
    message: str
    mesures: LectureCapteurDTO


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
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Base de données indisponible")
    return {"status": "ok"}


@router.post("/diagnostic", response_model=DiagnosticResponse)
def run_diagnostic(
    payload: DiagnosticRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    capteurs: CapteurHybridService = Depends(get_capteur_service),
):
    """Diagnostic d'un espace de l'utilisateur à partir de ses dernières mesures réelles."""
    espace = EspaceVertRepositoryImpl(db).get_for_user(payload.espace_id, current_user.id)
    if espace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Espace vert introuvable")
    lecture = LectureCapteurDTO.model_validate(capteurs.lecture_actuelle(espace))
    return DiagnosticResponse(statut=lecture.statut, message=MESSAGES.get(lecture.statut, ""), mesures=lecture)
