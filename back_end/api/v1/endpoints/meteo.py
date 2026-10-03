from fastapi import APIRouter, Depends, HTTPException, Query

from application.dto.meteo import MeteoDTO
from application.use_cases.meteo import obtenir_meteo_actuelle
from infrastructure.services.meteo_open_meteo import OpenMeteoService

router = APIRouter(prefix="/meteo", tags=["Météo Réelle"])

# Coordonnées de secours — utilisées uniquement si la géolocalisation du client échoue
COORDONNEES_VILLES = {
    "Saint-Priest": {"lat": 45.69, "lon": 4.94},
    "Lyon":          {"lat": 45.76, "lon": 4.83},
    "Paris":         {"lat": 48.85, "lon": 2.35},
    "Marseille":     {"lat": 43.29, "lon": 5.36},
}
VILLE_PAR_DEFAUT = "Lyon"


def get_meteo_service() -> OpenMeteoService:
    return OpenMeteoService()


@router.get("/actuelle", response_model=MeteoDTO)
def get_meteo_actuelle(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    meteo_service: OpenMeteoService = Depends(get_meteo_service),
):
    """Météo en temps réel par coordonnées GPS (Open-Meteo, sans clé API)."""
    try:
        return obtenir_meteo_actuelle(latitude=lat, longitude=lon, meteo_service=meteo_service)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur technique météo: {e}")


@router.get("/{ville}", response_model=MeteoDTO)
def get_meteo_ville(
    ville: str,
    meteo_service: OpenMeteoService = Depends(get_meteo_service),
):
    """Météo par nom de ville (fallback géolocalisation refusée côté client)."""
    coords = COORDONNEES_VILLES.get(ville, COORDONNEES_VILLES[VILLE_PAR_DEFAUT])
    try:
        return obtenir_meteo_actuelle(
            latitude=coords["lat"],
            longitude=coords["lon"],
            meteo_service=meteo_service,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail="Impossible de joindre le service météo.")
