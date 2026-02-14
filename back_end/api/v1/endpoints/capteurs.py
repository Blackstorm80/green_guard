# back_end/api/v1/endpoints/capteurs.py
from fastapi import APIRouter, Depends, Query
from typing import List

from application.use_cases.capteurs import obtenir_dashboard_capteurs
from infrastructure.services.capteur_hybrid_simulator import CapteurHybridSimulator
from infrastructure.services.meteo_open_meteo import OpenMeteoService
from api.v1.endpoints.meteo import get_meteo_service
from application.dto.capteurs import DashboardCapteursDTO

router = APIRouter(prefix="/capteurs", tags=["Capteurs"])

def get_capteur_service() -> CapteurHybridSimulator:
    # Pour l'instant, on instancie directement le simulateur.
    # Plus tard, on pourrait le rendre "singleton" pour qu'il garde son état.
    return CapteurHybridSimulator()

@router.get("/dashboard", response_model=DashboardCapteursDTO)
def dashboard_capteurs(
    espace_ids: List[int] = Query(default=[1, 2, 3, 4], description="Liste des IDs des espaces à interroger"),
    capteurs: CapteurHybridSimulator = Depends(get_capteur_service),
    meteo: OpenMeteoService = Depends(get_meteo_service)
):
    return obtenir_dashboard_capteurs(
        espace_ids=espace_ids,
        capteur_service=capteurs,
        meteo_service=meteo
    )