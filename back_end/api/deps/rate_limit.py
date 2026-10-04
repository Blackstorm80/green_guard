"""Limitation de débit en mémoire (fenêtre glissante).

Suffisant pour une instance d'API unique (cible v1). En multi-instances, remplacer
le stockage par Redis : les interfaces `__call__` des limiteurs restent les mêmes.

L'adresse du client est celle que fournit uvicorn : derrière un reverse proxy, elle n'est
juste que si ce proxy figure dans TRUSTED_PROXIES (--forwarded-allow-ips).
"""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

# Au-delà, les clés expirées sont purgées : des identifiants inventés ne font pas grossir la mémoire
MAX_CLES_AVANT_PURGE = 10_000
LONGUEUR_MAX_IDENTIFIANT = 254  # RFC 5321

# Message unique quel que soit le compteur atteint : un 429 ne révèle rien sur l'existence d'un compte
MESSAGE_429 = "Trop de tentatives. Réessayez dans quelques instants."


def _trop_de_tentatives(attente_s: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=MESSAGE_429,
        headers={"Retry-After": str(attente_s)},
    )


def _cle_ip(request: Request) -> str:
    ip = request.client.host if request.client else "inconnue"
    return f"ip:{ip}:{request.url.path}"


class RateLimiter:
    """Compteur par clé ; utilisé comme dépendance FastAPI, la clé est l'IP du client et la route."""

    def __init__(self, max_requetes: int, fenetre_s: int):
        self.max_requetes = max_requetes
        self.fenetre_s = fenetre_s
        self._appels: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def reinitialiser(self) -> None:
        with self._lock:
            self._appels.clear()

    def attente(self, cle: str) -> int:
        """Secondes à attendre avant une nouvelle tentative pour `cle` (0 : tentative permise)."""
        maintenant = time.monotonic()
        with self._lock:
            appels = self._appels.get(cle)
            if not appels:
                return 0
            self._expirer(appels, maintenant)
            if len(appels) < self.max_requetes:
                return 0
            return int(self.fenetre_s - (maintenant - appels[0])) + 1

    def enregistrer(self, cle: str) -> None:
        maintenant = time.monotonic()
        with self._lock:
            if len(self._appels) >= MAX_CLES_AVANT_PURGE:
                for cle_existante in list(self._appels):
                    if not self._expirer(self._appels[cle_existante], maintenant):
                        del self._appels[cle_existante]
            self._appels[cle].append(maintenant)

    def _expirer(self, appels: deque, maintenant: float) -> deque:
        while appels and maintenant - appels[0] > self.fenetre_s:
            appels.popleft()
        return appels

    def consommer(self, cle: str) -> None:
        attente = self.attente(cle)
        if attente:
            raise _trop_de_tentatives(attente)
        self.enregistrer(cle)

    def __call__(self, request: Request) -> None:
        self.consommer(_cle_ip(request))


class LimiteurConnexion:
    """Connexion : deux compteurs, un large par IP et un strict par identifiant (e-mail normalisé).

    Un attaquant ne peut plus bloquer toute une collectivité derrière une même IP de sortie,
    et le bourrage d'identifiants sur un compte reste freiné quelle que soit l'IP d'origine.
    Une tentative refusée n'est décomptée dans aucun des deux compteurs.
    """

    def __init__(self, max_par_ip: int, max_par_identifiant: int, fenetre_s: int):
        self.par_ip = RateLimiter(max_par_ip, fenetre_s)
        self.par_identifiant = RateLimiter(max_par_identifiant, fenetre_s)

    def reinitialiser(self) -> None:
        self.par_ip.reinitialiser()
        self.par_identifiant.reinitialiser()

    def __call__(self, request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> None:
        cle_ip = _cle_ip(request)
        # Compteur indépendant de l'existence du compte : même traitement pour un e-mail inconnu
        identifiant = form_data.username.strip().lower()[:LONGUEUR_MAX_IDENTIFIANT]
        cle_identifiant = f"identifiant:{identifiant}"
        attente = max(self.par_ip.attente(cle_ip), self.par_identifiant.attente(cle_identifiant))
        if attente:
            raise _trop_de_tentatives(attente)
        self.par_ip.enregistrer(cle_ip)
        self.par_identifiant.enregistrer(cle_identifiant)
