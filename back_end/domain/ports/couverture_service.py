# back_end/domain/ports/couverture_service.py

from abc import ABC, abstractmethod
from domain.models import EspaceVert


class ICouverturePilotageService(ABC):
    """
    Port pour piloter la couverture physique (ombrage) d'un espace vert.
    """

    @abstractmethod
    def ajuster_couverture_pour_protection(
        self,
        espace: EspaceVert,
    ) -> None:
        """
        Ajuste la couverture de l'espace (fermer/ouvrir, changer le niveau)
        en fonction des caractéristiques des plantes et des conditions
        (ensoleillement, chaleur, etc.).
        """
        ...
