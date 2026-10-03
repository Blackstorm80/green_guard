import logging
import time
from datetime import datetime
from threading import Lock

import requests

from domain.ports.meteo import ConditionsMeteo, IMeteoService, MeteoIndisponibleError

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_S = 10
# Cache par point arrondi (~10 km) : évite de dépasser le quota gratuit Open-Meteo
# quand de nombreux espaces sont proches les uns des autres.
CACHE_TTL_S = 15 * 60
PRECISION_CACHE = 1

_cache: dict[tuple[float, float], tuple[float, ConditionsMeteo]] = {}
_cache_lock = Lock()


class OpenMeteoService(IMeteoService):
    def recuperer_conditions_actuelles(self, latitude, longitude, maintenant: datetime) -> ConditionsMeteo:
        cle = (round(latitude, PRECISION_CACHE), round(longitude, PRECISION_CACHE))
        with _cache_lock:
            entree = _cache.get(cle)
            if entree and time.monotonic() - entree[0] < CACHE_TTL_S:
                return entree[1]

        conditions = self._appeler_api(latitude, longitude)
        with _cache_lock:
            _cache[cle] = (time.monotonic(), conditions)
        return conditions

    @staticmethod
    def _appeler_api(latitude: float, longitude: float) -> ConditionsMeteo:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,cloud_cover",
            "daily": "et0_fao_evapotranspiration,precipitation_sum",
            "forecast_days": 1,
            "timezone": "auto",
        }
        try:
            response = requests.get(OPEN_METEO_URL, params=params, timeout=TIMEOUT_S)
            response.raise_for_status()
            data = response.json()
            current = data["current"]
            daily = data.get("daily", {})
        except (requests.RequestException, ValueError, KeyError) as exc:
            logger.warning("Open-Meteo indisponible (%s, %s) : %s", latitude, longitude, exc)
            raise MeteoIndisponibleError("Service météo indisponible") from exc

        cloud_cover = current.get("cloud_cover", 100)
        ensoleillement_fort = cloud_cover < 30
        et0 = (daily.get("et0_fao_evapotranspiration") or [None])[0]
        pluie = (daily.get("precipitation_sum") or [0.0])[0] or 0.0

        return ConditionsMeteo(
            city="Station Open-Meteo",
            temperature_c=current.get("temperature_2m"),
            condition="Dégagé" if ensoleillement_fort else "Nuageux",
            ensoleillement_fort=ensoleillement_fort,
            humidite=current.get("relative_humidity_2m"),
            pluie_jour_mm=pluie,
            et0_jour_mm=et0,
        )
