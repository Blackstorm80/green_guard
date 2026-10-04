from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps.auth import get_current_user
from api.v1.endpoints.meteo import get_meteo_service
from application.dto.capteurs import DashboardCapteursDTO
from application.use_cases.capteurs import obtenir_dashboard_capteurs
from application.use_cases.secheresse import restrictions_en_vigueur
from config import settings
from domain.logic.secheresse import regles_depuis_parametres
from domain.models import User
from infrastructure.database import get_db
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.repositories.restriction_secheresse_repository_impl import RestrictionSecheresseRepositoryImpl
from infrastructure.services.capteur_hybrid_service import CapteurHybridService
from infrastructure.services.meteo_open_meteo import OpenMeteoService

router = APIRouter()


def get_capteur_service(db: Session = Depends(get_db)) -> CapteurHybridService:
    return CapteurHybridService(db_session=db)


@router.get("/dashboard", response_model=DashboardCapteursDTO)
def dashboard_capteurs(
    espace_ids: list[int] | None = Query(
        None, description="Filtre optionnel ; par défaut tous les espaces de l'organisation."
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    capteurs: CapteurHybridService = Depends(get_capteur_service),
    meteo: OpenMeteoService = Depends(get_meteo_service),
):
    espaces = EspaceVertRepositoryImpl(db).list_resume_par_organisation(current_user.organisation_id)
    if espace_ids:
        # Filtre appliqué sur les espaces de l'organisation : impossible de lire ceux d'une autre
        demandes = set(espace_ids)
        espaces = [e for e in espaces if e.id in demandes]
    restrictions = restrictions_en_vigueur(
        [e.id for e in espaces], datetime.now(settings.fuseau).date(), RestrictionSecheresseRepositoryImpl(db))
    return obtenir_dashboard_capteurs(espaces=espaces, capteur_service=capteurs, meteo_service=meteo,
                                      fuseau=settings.fuseau,
                                      regles=regles_depuis_parametres(current_user.organisation.parametres),
                                      restrictions=restrictions)
