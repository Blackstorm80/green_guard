import logging
import math
import time
from datetime import date, datetime, timedelta
from threading import Lock
from zoneinfo import ZoneInfo

import requests

from config import settings
from domain.ports.meteo import (
    HORIZON_PREVISION_JOURS,
    SERIE_JOURS_MAX,
    ConditionsMeteo,
    IMeteoService,
    MeteoIndisponibleError,
    MeteoJournaliere,
    PrevisionJournaliere,
)

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_S = 10
# Cache par point arrondi (~10 km) : évite de dépasser le quota gratuit Open-Meteo
# quand de nombreux espaces sont proches les uns des autres.
CACHE_TTL_S = 15 * 60
PRECISION_CACHE = 1
SOURCE = "open-meteo"

# Prévision : premier jour renvoyé = aujourd'hui (fuseau demandé), d'où 8 jours pour couvrir J..J+7
JOURS_PREVISION = HORIZON_PREVISION_JOURS + 1
# Échec mémorisé brièvement (prévision) : un fournisseur en panne ne coûte pas un délai d'attente
# à chaque lecture du tableau de bord
ECHEC_TTL_S = 60
# Au-delà, chaque écriture purge les entrées expirées (coordonnées libres de /meteo/actuelle)
CACHE_MAX_ENTREES = 1000
# Bornes de plausibilité des cumuls journaliers prévus : au-delà, la réponse est jugée inexploitable
ET0_MAX_MM = 30.0
PLUIE_MAX_MM = 1000.0

# Clé : point arrondi (conditions du jour), point arrondi + plage de dates (série passée),
# ou point arrondi + "prevision" + jour métier (une prévision mise en cache la veille ne couvre
# plus J..J+7 après minuit). Valeur : (échéance monotone, donnée ou échec mémorisé)
_cache: dict[tuple, tuple[float, object]] = {}
_cache_lock = Lock()
_verrous_par_point: dict[tuple, Lock] = {}


class _Echec:
    def __init__(self, message: str):
        self.message = message


def _lire_cache(cle: tuple):
    with _cache_lock:
        entree = _cache.get(cle)
    if entree is None or time.monotonic() >= entree[0]:
        return None
    if isinstance(entree[1], _Echec):
        raise MeteoIndisponibleError(entree[1].message)
    return entree[1]


def _purger_expirees(maintenant: float) -> None:
    """Sous _cache_lock. Un verrou retiré pendant qu'un appel l'attend coûte au pire un appel en double."""
    for cle in [c for c, (echeance, _) in _cache.items() if echeance <= maintenant]:
        del _cache[cle]
    for cle in [c for c, verrou in _verrous_par_point.items() if c not in _cache and not verrou.locked()]:
        del _verrous_par_point[cle]


def _ecrire_cache(cle: tuple, valeur: object, duree_s: float) -> None:
    with _cache_lock:
        maintenant = time.monotonic()
        if len(_cache) >= CACHE_MAX_ENTREES:
            _purger_expirees(maintenant)
        _cache[cle] = (maintenant + duree_s, valeur)


def _nombre(valeur, minimum: float, maximum: float) -> float | None:
    """Valeur numérique finie et plausible du fournisseur (None conservé) ; sinon ValueError."""
    if valeur is None:
        return None
    if isinstance(valeur, bool) or not isinstance(valeur, int | float):
        raise ValueError(f"valeur non numérique : {valeur!r}")
    valeur = float(valeur)
    if not math.isfinite(valeur) or not minimum <= valeur <= maximum:
        raise ValueError(f"valeur hors bornes : {valeur!r}")
    return valeur


def _avec_cache(cle: tuple, charger, memoriser_echec: bool = False):
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
        try:
            valeur = charger()
        except MeteoIndisponibleError as exc:
            if memoriser_echec:
                _ecrire_cache(cle, _Echec(str(exc)), ECHEC_TTL_S)
            raise
        _ecrire_cache(cle, valeur, CACHE_TTL_S)
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

    def recuperer_prevision_journaliere(self, latitude, longitude) -> list[PrevisionJournaliere]:
        aujourd_hui = datetime.now(ZoneInfo(self.fuseau_horaire)).date()
        cle = (round(latitude, PRECISION_CACHE), round(longitude, PRECISION_CACHE), "prevision", aujourd_hui)
        return _avec_cache(cle, lambda: self._appeler_prevision(latitude, longitude), memoriser_echec=True)

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

    def _appeler_prevision(self, latitude: float, longitude: float) -> list[PrevisionJournaliere]:
        data = self._get({
            "latitude": latitude,
            "longitude": longitude,
            "daily": "et0_fao_evapotranspiration,precipitation_sum,precipitation_probability_max",
            "forecast_days": JOURS_PREVISION,
            "timezone": self.fuseau_horaire,
        })
        try:
            daily = data["daily"]
            jours = [date.fromisoformat(j) for j in daily["time"]]
            et0 = daily.get("et0_fao_evapotranspiration") or [None] * len(jours)
            pluie = daily.get("precipitation_sum") or [None] * len(jours)
            probabilite = daily.get("precipitation_probability_max") or [None] * len(jours)
            return [
                PrevisionJournaliere(
                    jour=j, et0_mm=_nombre(e, 0.0, ET0_MAX_MM), pluie_mm=_nombre(p, 0.0, PLUIE_MAX_MM) or 0.0,
                    probabilite_pluie_pct=_nombre(pp, 0.0, 100.0), source=SOURCE,
                )
                for j, e, p, pp in zip(jours, et0, pluie, probabilite, strict=False)
            ]
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            logger.warning("Prévision Open-Meteo illisible (%s, %s) : %s", latitude, longitude, exc)
            raise MeteoIndisponibleError("Prévision météo inexploitable") from exc

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
