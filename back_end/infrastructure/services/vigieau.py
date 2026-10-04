"""Client de l'API publique VigiEau (restrictions sécheresse), sans clé.

Point d'entrée vérifié sur le dépôt MTES-MCT/vigieau-api (README et src/zones/zones.service.ts, branche master) :
GET {VIGIEAU_URL}?lon=…&lat=…&profil=collectivite&zoneType=AEP|SOU|SUP
- réponse 200 : liste des zones d'alerte qui contiennent le point (liste vide : aucune restriction) ;
  chaque zone porte type (AEP eau potable, SOU souterraine, SUP superficielle), niveauGravite
  (vigilance, alerte, alerte_renforcee, crise), nom, code et arrete (id, cheminFichier…) ;
- avec zoneType, au plus une zone ; sans zoneType, toutes (la plus sévère est retenue) ;
- 400 : coordonnées invalides ; 500 : plusieurs zones de même type au point (données VigiEau).
  Dans le code source, la recherche par lon/lat ne lève jamais 404 (liste vide sans zone), même si le README
  annonce un 404 « aucune zone d'alerte en vigueur ». Un 404 est donc une erreur pour ce point, jamais
  « aucune restriction » (un registre ne doit pas certifier une absence de restriction qu'il n'a pas lue) :
  route inconnue (VIGIEAU_URL mal saisie) ou changement de comportement de l'API. Il n'interrompt pas à lui
  seul une actualisation (trois erreurs de suite le font) ; une actualisation sans aucun niveau lu est
  journalisée en erreur. Seule une liste JSON vaut réponse VigiEau.
Profil « collectivite » : le profil des collectivités existe ; il ne filtre que la liste des usages, pas le niveau.

Le type de zone suit la source d'eau de l'espace (domain/logic/secheresse.py : TYPE_ZONE_PAR_SOURCE).
Cache par point et par jour (fuseau métier) : un niveau change au plus une fois par jour (arrêtés
préfectoraux). Un échec est mémorisé une minute pour ne pas répéter un délai d'attente.
Aucune redirection n'est suivie : l'URL est fixée par l'exploitant (config) et seuls lat/lon, bornés, varient.
"""
import logging
import math
import time
from datetime import date, datetime
from threading import Lock

import requests

from config import settings
from domain.logic.secheresse import AUCUNE, NIVEAUX_VIGIEAU, RANG_NIVEAU
from domain.ports.vigieau import IVigieauService, NiveauVigieau, VigieauIndisponibleError, VigieauInjoignableError

logger = logging.getLogger(__name__)

PROFIL = "collectivite"
TYPES_ZONE = ("AEP", "SOU", "SUP")
PRECISION_CACHE = 5            # ~1 m : les limites de zones d'alerte passent entre deux parcs voisins
ECHEC_TTL_S = 60
CACHE_MAX_ENTREES = 5000
LONGUEUR_MAX_URL = 500
# Réponses qui valent pour tous les points (passerelle en panne) : inutile d'insister
STATUTS_PANNE_GENERALE = {502, 503, 504}

_cache: dict[tuple, tuple[float, object]] = {}   # clé → (échéance monotone, NiveauVigieau ou erreur)
_cache_lock = Lock()


def vider_cache() -> None:
    with _cache_lock:
        _cache.clear()


def _texte(valeur, longueur: int) -> str | None:
    if valeur is None or isinstance(valeur, bool):
        return None
    return str(valeur).strip()[:longueur] or None


def _url_sure(valeur) -> str | None:
    """Lien vers l'arrêté affiché dans l'interface : https seulement (jamais javascript: ou data:)."""
    if isinstance(valeur, str) and valeur.startswith("https://") and len(valeur) <= LONGUEUR_MAX_URL:
        return valeur
    return None


def interpreter_zones(donnees, type_zone: str | None) -> NiveauVigieau:
    """Zone retenue dans la réponse ; lève VigieauIndisponibleError si la réponse est inexploitable."""
    if not isinstance(donnees, list):
        raise VigieauIndisponibleError("Réponse VigiEau inexploitable (liste de zones attendue)")
    zones = []
    for zone in donnees:
        if not isinstance(zone, dict):
            raise VigieauIndisponibleError("Réponse VigiEau inexploitable (zone illisible)")
        niveau = zone.get("niveauGravite")
        if niveau is None:
            continue   # entrée « arrêté municipal » seul, sans zone d'alerte
        if niveau not in NIVEAUX_VIGIEAU:
            raise VigieauIndisponibleError(f"Niveau VigiEau inconnu : {str(niveau)[:40]!r}")
        if type_zone is None or zone.get("type") == type_zone:
            zones.append(zone)
    if not zones:
        return NiveauVigieau(niveau=AUCUNE, type_zone=type_zone)
    zone = max(zones, key=lambda z: RANG_NIVEAU[z["niveauGravite"]])
    arrete = zone.get("arrete") if isinstance(zone.get("arrete"), dict) else {}
    return NiveauVigieau(
        niveau=zone["niveauGravite"],
        type_zone=zone.get("type") if zone.get("type") in TYPES_ZONE else type_zone,
        zone_nom=_texte(zone.get("nom"), 255),
        zone_code=_texte(zone.get("code"), 60),
        arrete_identifiant=_texte(arrete.get("id"), 40),
        arrete_url=_url_sure(arrete.get("cheminFichier")),
    )


class VigieauService(IVigieauService):
    def __init__(self, url: str | None = None, timeout_s: float | None = None):
        self.url = url or settings.vigieau_url
        self.timeout_s = timeout_s or settings.vigieau_timeout_s

    def niveau_au_point(self, latitude: float, longitude: float, type_zone: str | None) -> NiveauVigieau:
        if not (math.isfinite(latitude) and math.isfinite(longitude)
                and -85 < latitude < 85 and -180 < longitude < 180):
            raise VigieauIndisponibleError("Coordonnées hors du domaine couvert par VigiEau")
        if type_zone is not None and type_zone not in TYPES_ZONE:
            raise ValueError(f"Type de zone inconnu : {type_zone}")
        jour = datetime.now(settings.fuseau).date()
        cle = (round(latitude, PRECISION_CACHE), round(longitude, PRECISION_CACHE), type_zone, jour)
        en_cache = self._lire_cache(cle)
        if en_cache is not None:
            return en_cache
        try:
            niveau = self._appeler(latitude, longitude, type_zone)
        except VigieauIndisponibleError as exc:
            self._ecrire_cache(cle, exc, ECHEC_TTL_S, jour)
            raise
        self._ecrire_cache(cle, niveau, None, jour)
        return niveau

    def _appeler(self, latitude: float, longitude: float, type_zone: str | None) -> NiveauVigieau:
        params = {"lon": f"{longitude:.6f}", "lat": f"{latitude:.6f}", "profil": PROFIL}
        if type_zone:
            params["zoneType"] = type_zone
        try:
            reponse = requests.get(self.url, params=params, timeout=self.timeout_s, allow_redirects=False,
                                   headers={"Accept": "application/json"})
        except requests.RequestException as exc:
            logger.warning("VigiEau injoignable (%.4f, %.4f) : %s", latitude, longitude, exc)
            raise VigieauInjoignableError("Service VigiEau injoignable") from exc
        if reponse.status_code != 200:
            logger.warning("VigiEau : réponse %s pour (%.4f, %.4f)", reponse.status_code, latitude, longitude)
            if reponse.status_code in STATUTS_PANNE_GENERALE:
                raise VigieauInjoignableError(f"Service VigiEau indisponible (HTTP {reponse.status_code})")
            raise VigieauIndisponibleError(f"Service VigiEau en erreur (HTTP {reponse.status_code})")
        try:
            donnees = reponse.json()
        except ValueError as exc:
            raise VigieauIndisponibleError("Réponse VigiEau illisible (JSON attendu)") from exc
        return interpreter_zones(donnees, type_zone)

    @staticmethod
    def _lire_cache(cle: tuple) -> NiveauVigieau | None:
        with _cache_lock:
            entree = _cache.get(cle)
        if entree is None or time.monotonic() >= entree[0]:
            return None
        if isinstance(entree[1], VigieauIndisponibleError):
            raise type(entree[1])(str(entree[1]))
        return entree[1]

    @staticmethod
    def _ecrire_cache(cle: tuple, valeur: object, duree_s: float | None, jour: date) -> None:
        """duree_s None : valable jusqu'au changement de jour (la clé porte le jour)."""
        with _cache_lock:
            if len(_cache) >= CACHE_MAX_ENTREES:
                maintenant = time.monotonic()
                for ancienne in [c for c, (echeance, _) in _cache.items() if c[3] != jour or echeance <= maintenant]:
                    del _cache[ancienne]
                if len(_cache) >= CACHE_MAX_ENTREES:
                    _cache.clear()
            _cache[cle] = (time.monotonic() + duree_s if duree_s else math.inf, valeur)
