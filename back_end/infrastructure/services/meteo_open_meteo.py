import logging
import time
from datetime import date, datetime, timedelta
from threading import Lock

import requests

from config import settings
from domain.ports.meteo import (
    SERIE_JOURS_MAX,
    ConditionsMeteo,
    IMeteoService,
    MeteoIndisponibleError,
    MeteoJournaliere,
)

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_S = 10
# Cache par point arrondi (~10 km) : évite de dépasser le quota gratuit Open-Meteo
# quand de nombreux espaces sont proches les uns des autres.
CACHE_TTL_S = 15 * 60
PRECISION_CACHE = 1
SOURCE = "open-meteo"

# Clé : point arrondi (conditions du jour), ou point arrondi + plage de dates (série passée)
_cache: dict[tuple, tuple[float, object]] = {}
_cache_lock = Lock()
_verrous_par_point: dict[tuple, Lock] = {}


def _lire_cache(cle: tuple):
    with _cache_lock:
        entree = _cache.get(cle)
    if entree and time.monotonic() - entree[0] < CACHE_TTL_S:
        return entree[1]
    return None


def _avec_cache(cle: tuple, charger):
    """Un seul appel réseau par clé : les requêtes concurrentes attendent puis lisent le cache."""
    valeur = _lire_cache(cle)
    if valeur is not None:
        return valeur
    with _cache_lock:
        verrou = _verrous_par_point.setdefault(cle, Lock())
    with verrou:
        valeur = _lire_cache(cle)
        if valeur is not None:
            return valeur
        valeur = charger()
        with _cache_lock:
            _cache[cle] = (time.monotonic(), valeur)
        return valeur


class OpenMeteoService(IMeteoService):
    def __init__(self, fuseau_horaire: str | None = None):
        # Cumuls journaliers (pluie, ET0) calculés sur le jour du fuseau métier, comme le bilan
        self.fuseau_horaire = fuseau_horaire or settings.fuseau_horaire

    def recuperer_conditions_actuelles(self, latitude, longitude, maintenant: datetime) -> ConditionsMeteo:
        cle = (round(latitude, PRECISION_CACHE), round(longitude, PRECISION_CACHE))
        return _avec_cache(cle, lambda: self._appeler_api(latitude, longitude))

    def recuperer_serie_journaliere(self, latitude, longitude, debut: date, fin: date) -> list[MeteoJournaliere]:
        if fin < debut or (fin - debut).days >= SERIE_JOURS_MAX:
            raise ValueError(f"Plage de dates invalide : {debut} → {fin} ({SERIE_JOURS_MAX} jours au plus)")
        cle = (round(latitude, PRECISION_CACHE), round(longitude, PRECISION_CACHE), debut, fin)
        return _avec_cache(cle, lambda: self._appeler_serie(latitude, longitude, debut, fin))

    def _get(self, params: dict) -> dict:
        try:
            response = requests.get(OPEN_METEO_URL, params=params, timeout=TIMEOUT_S)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Open-Meteo indisponible (%s, %s) : %s", params["latitude"], params["longitude"], exc)
            raise MeteoIndisponibleError("Service météo indisponible") from exc

    def _appeler_serie(self, latitude: float, longitude: float, debut: date, fin: date) -> list[MeteoJournaliere]:
        # start_date/end_date sur l'API de prévision : jours passés (92 au plus) dans le fuseau métier
        data = self._get({
            "latitude": latitude,
            "longitude": longitude,
            "daily": "et0_fao_evapotranspiration,precipitation_sum",
            "start_date": debut.isoformat(),
            "end_date": fin.isoformat(),
            "timezone": self.fuseau_horaire,
        })
        try:
            daily = data["daily"]
            jours = [date.fromisoformat(j) for j in daily["time"]]
            et0 = daily.get("et0_fao_evapotranspiration") or [None] * len(jours)
            pluie = daily.get("precipitation_sum") or [None] * len(jours)
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Série Open-Meteo illisible (%s, %s) : %s", latitude, longitude, exc)
            raise MeteoIndisponibleError("Réponse météo inexploitable") from exc
        attendus = {debut + timedelta(days=i) for i in range((fin - debut).days + 1)}
        return [
            MeteoJournaliere(jour=j, et0_mm=e, pluie_mm=p or 0.0, source=SOURCE)
            for j, e, p in zip(jours, et0, pluie, strict=False) if j in attendus
        ]

    def _appeler_api(self, latitude: float, longitude: float) -> ConditionsMeteo:
        data = self._get({
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,cloud_cover",
            "daily": "et0_fao_evapotranspiration,precipitation_sum",
            "forecast_days": 1,
            "timezone": self.fuseau_horaire,
        })
        try:
            current = data["current"]
            daily = data.get("daily", {})
        except (KeyError, TypeError, AttributeError) as exc:
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
            source=SOURCE,
        )
