from datetime import UTC, datetime

from application.dto.meteo import MeteoDTO
from domain.ports.meteo import IMeteoService


def obtenir_meteo_actuelle(latitude: float, longitude: float, meteo_service: IMeteoService) -> MeteoDTO:
    """Météo actuelle d'un point. Propage MeteoIndisponibleError."""
    conditions = meteo_service.recuperer_conditions_actuelles(
        latitude=latitude,
        longitude=longitude,
        maintenant=datetime.now(UTC),
    )
    return MeteoDTO(
        city=conditions.city,
        temperature_c=conditions.temperature_c,
        condition=conditions.condition,
        icon=None,
        ensoleillement_fort=conditions.ensoleillement_fort,
    )
