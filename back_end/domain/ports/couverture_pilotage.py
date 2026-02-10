# back_end/domain/ports/couverture_pilotage.py

from __future__ import annotations

from abc import ABC, abstractmethod

from back_end.domain.entities import EspaceVertEntity


class ICouverturePilotageService(ABC):
    """
    Port de domaine pour piloter la couverture physique (ombrage) d'un espace vert.
    Une implémentation concrète pourra commander un voile d'ombrage, un store,
    mettre à jour un état IoT, etc.
    """

    @abstractmethod
    def ajuster_couverture_pour_protection(self, espace: EspaceVertEntity) -> None:
        """
        Ajuste la couverture de l'espace pour protéger les plantes :
        fermer/ouvrir, augmenter le niveau d'ombre, etc.
        """
        ...
