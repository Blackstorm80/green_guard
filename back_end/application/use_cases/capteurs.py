# back_end/application/use_cases/capteurs.py
from datetime import datetime
from typing import List

from domain.ports.capteurs import ICapteurService
from domain.ports.meteo import IMeteoService
from application.dto.capteurs import DashboardCapteursDTO, LectureCapteurDTO


def _calculer_sante_globale(capteurs: List[LectureCapteurDTO]) -> float:
    """Calcule un score de santé global basé sur la réserve en eau moyenne."""
    if not capteurs:
        return 100.0
    # On suppose que la réserve max est 100mm. Le score est la moyenne des réserves.
    total_reserve = sum(c.reserve_eau_mm for c in capteurs)
    sante = (total_reserve / len(capteurs))
    return round(sante, 1)

def _determiner_qualite_air(capteurs: List[LectureCapteurDTO]) -> str:
    """Détermine la qualité de l'air globale basée sur le CO2 moyen."""
    if not capteurs:
        return "Inconnue"
    co2_moyen = sum(c.co2_ppm for c in capteurs) / len(capteurs)
    if co2_moyen < 800:
        return "Bonne"
    if co2_moyen < 1200:
        return "Moyenne"
    return "Mauvaise"

def obtenir_dashboard_capteurs(
    espace_ids: List[int],
    capteur_service: ICapteurService,
    meteo_service: IMeteoService,
    latitude: float = 45.7640,  # Lyon
    longitude: float = 4.8357
) -> DashboardCapteursDTO:
    
    # Météo réelle
    meteo_reelle = meteo_service.recuperer_conditions_actuelles(latitude, longitude, datetime.utcnow())
    
    # Lectures capteurs
    capteurs = []
    for espace_id in espace_ids:
        lecture = capteur_service.lecture_actuelle(espace_id)
        if lecture:
            capteurs.append(LectureCapteurDTO.from_orm(lecture))
    
    # Metrics agrégés
    metrics = {
        "sante_globale_percent": _calculer_sante_globale(capteurs),
        "espaces_stress": sum(1 for c in capteurs if c.reserve_eau_mm < 20),
        "co2_moyen_ppm": int(sum(c.co2_ppm for c in capteurs) / len(capteurs)) if capteurs else 0,
        "qualite_air": _determiner_qualite_air(capteurs)
    }
    
    return DashboardCapteursDTO(
        meteo_exterieure={
            "city": meteo_reelle.city,
            "temperature_c": meteo_reelle.temperature_c,
            "condition": meteo_reelle.condition
        },
        capteurs=capteurs,
        metrics=metrics
    )