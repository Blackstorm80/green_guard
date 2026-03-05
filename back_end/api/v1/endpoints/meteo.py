from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any

from application.dto.meteo import MeteoDTO
from application.use_cases.meteo import obtenir_meteo_actuelle
from infrastructure.services.meteo_open_meteo import OpenMeteoService
# back_end/api/v1/endpoints/meteo.py

# key meteo temporaire le juste pour le demo le temps que je trouve uen best way de pour les stockées
METEO_API_KEY = "2c962fb7d104ab1b2f65f15f44eac098"
router = APIRouter(prefix="/meteo", tags=["Météo Réelle"])

# Dictionnaire de secours pour transformer une ville en coordonnées pour le service
COORDONNEES_VILLES = {
    "Saint-Priest": {"lat": 45.69, "lon": 4.94},
    "Lyon": {"lat": 45.76, "lon": 4.83},
    "Paris": {"lat": 48.85, "lon": 2.35},
    "Marseille": {"lat": 43.29, "lon": 5.36}
}

def get_meteo_service() -> OpenMeteoService:
    """Injection de dépendance pour le service Open-Meteo."""
    return OpenMeteoService()

@router.get("/actuelle", response_model=MeteoDTO)
def get_meteo_actuelle(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    meteo_service: OpenMeteoService = Depends(get_meteo_service),
):
    """Récupère la météo exacte par coordonnées GPS."""
    try:
        return obtenir_meteo_actuelle(
            latitude=lat,
            longitude=lon,
            meteo_service=meteo_service,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur technique météo: {e}")

@router.get("/{ville}")
def get_meteo_ville(
    ville: str,
    meteo_service: OpenMeteoService = Depends(get_meteo_service)
):
    """
    Récupère les VRAIES données météo pour une ville donnée 
    en utilisant le service Open-Meteo.
    """
    # 1. On cherche les coordonnées de la ville
    coords = COORDONNEES_VILLES.get(ville)
    
    if not coords:
        # Si la ville n'est pas dans notre liste, on prend Lyon par défaut pour la démo
        coords = COORDONNEES_VILLES["Lyon"]

    try:
        # 2. On utilise ton Use Case (Le cœur de l'oignon)
        data = obtenir_meteo_actuelle(
            latitude=coords["lat"],
            longitude=coords["lon"],
            meteo_service=meteo_service,
        )
        
        # 3. On formate la réponse pour ton Frontend
        # (Adapte les noms de champs selon ce que renvoie ton MeteoDTO)
        return {
            "temp": data.temperature if hasattr(data, 'temperature') else data.get('temperature'),
            "condition": "Ciel dégagé", # Open-Meteo renvoie des codes (WMO), on simplifie ici
            "humidite": data.humidite if hasattr(data, 'humidite') else data.get('humidite'),
            "vent": data.vitesse_vent if hasattr(data, 'vitesse_vent') else data.get('vitesse_vent'),
            "ville": ville
        }
    except Exception as e:
        print(f"Erreur météo réelle : {e}")
        raise HTTPException(status_code=502, detail="Impossible de joindre le service météo réel.")