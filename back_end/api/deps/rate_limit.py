"""Limitation de débit en mémoire (fenêtre glissante), par IP et par route.

Suffisant pour une instance d'API unique (cible v1). En multi-instances, remplacer
le stockage par Redis : l'interface `RateLimiter.__call__` reste la même.
"""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requetes: int, fenetre_s: int):
        self.max_requetes = max_requetes
        self.fenetre_s = fenetre_s
        self._appels: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def reinitialiser(self) -> None:
        with self._lock:
            self._appels.clear()

    def __call__(self, request: Request) -> None:
        ip = request.client.host if request.client else "inconnue"
        cle = f"{ip}:{request.url.path}"
        maintenant = time.monotonic()
        with self._lock:
            appels = self._appels[cle]
            while appels and maintenant - appels[0] > self.fenetre_s:
                appels.popleft()
            if len(appels) >= self.max_requetes:
                attente = int(self.fenetre_s - (maintenant - appels[0])) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Trop de tentatives. Réessayez dans quelques instants.",
                    headers={"Retry-After": str(attente)},
                )
            appels.append(maintenant)
