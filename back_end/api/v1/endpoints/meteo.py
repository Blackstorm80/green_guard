# back_end/api/v1/endpoints/meteo.py
from fastapi import APIRouter, Depends, HTTPException, Query

from application.dto.meteo import MeteoDTO
from application.use_cases.meteo import obtenir_meteo_actuelle
from infrastructure.services.meteo_open_meteo import OpenMeteoService
from domain.ports.meteo import IMeteoService

router = APIRouter(prefix="/meteo", tags=["Météo"])


def get_meteo_service() -> OpenMeteoService:
    # ici on pourrait injecter config, clé API, etc.
    return OpenMeteoService()


@router.get("/actuelle", response_model=MeteoDTO)
def get_meteo_actuelle(
    lat: float = Query(..., description="Latitude en degrés décimaux"),
    lon: float = Query(..., description="Longitude en degrés décimaux"),
    meteo_service: OpenMeteoService = Depends(get_meteo_service),
):
    try:
        return obtenir_meteo_actuelle(
            latitude=lat,
            longitude=lon,
            meteo_service=meteo_service,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur service météo: {e}")
