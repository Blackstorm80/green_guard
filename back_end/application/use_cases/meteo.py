# back_end/application/use_cases/meteo.py
from datetime import datetime
from domain.ports.meteo import IMeteoService
from application.dto.meteo import MeteoDTO


def obtenir_meteo_actuelle(
    latitude: float,
    longitude: float,
    meteo_service: IMeteoService,
) -> MeteoDTO:
    """
    Use case : retourne la météo actuelle pour une position (lat, lon)
    sous forme de DTO pour le front.
    """

    maintenant = datetime.utcnow()
    conditions = meteo_service.recuperer_conditions_actuelles(
        latitude=latitude,
        longitude=longitude,
        maintenant=maintenant,
    )

    # Mapping ConditionsMeteo -> MeteoDTO
    return MeteoDTO(
        city=conditions.city,
        temperature_c=conditions.temperature_c,
        condition=conditions.condition,
        icon=None,  # tu pourras mapper condition -> icône côté front si tu veux
        ensoleillement_fort=conditions.ensoleillement_fort,
    )