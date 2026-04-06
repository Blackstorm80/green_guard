# back_end/api/v1/endpoints/capteurs.py
from fastapi import APIRouter, Depends, Query
from typing import List
from sqlalchemy.orm import Session # AJOUTE CET IMPORT

from application.use_cases.capteurs import obtenir_dashboard_capteurs
from infrastructure.services.capteur_hybrid_service import CapteurHybridService
from infrastructure.services.meteo_open_meteo import OpenMeteoService
from api.v1.endpoints.meteo import get_meteo_service

# VÉRIFIE LE CHEMIN DE TON DEPS DB (souvent api/deps/db.py ou api/deps.py)
from infrastructure.database import get_db 

from application.dto.capteurs import DashboardCapteursDTO
from api.deps.auth import get_current_user
from domain.models import User

router = APIRouter(prefix="/capteurs", tags=["Capteurs"])

# MODIFICATION ICI : On injecte la DB
def get_capteur_service(db: Session = Depends(get_db)) -> CapteurHybridService:
    # On passe la session db au constructeur du service
    return CapteurHybridService(db_session=db)

@router.get("/dashboard", response_model=DashboardCapteursDTO)
def dashboard_capteurs(
    espace_ids: List[int] = Query(default=[1, 2, 3, 4]),
    current_user: User = Depends(get_current_user),
    # FastAPI s'occupe maintenant de cascader la DB vers le service
    capteurs: CapteurHybridService = Depends(get_capteur_service),
    meteo: OpenMeteoService = Depends(get_meteo_service)
):
    return obtenir_dashboard_capteurs(
        espace_ids=espace_ids,
        capteur_service=capteurs,
        meteo_service=meteo
    )