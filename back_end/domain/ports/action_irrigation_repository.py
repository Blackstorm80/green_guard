from abc import ABC, abstractmethod
from datetime import datetime

from domain.models import ActionIrrigation


class IActionIrrigationRepository(ABC):
    """Apports d'eau comptés dans le bilan. Les écritures ne valident pas la transaction : l'appelant
    les valide avec l'intervention qui les produit (tout ou rien)."""

    @abstractmethod
    def get_par_intervention(self, intervention_id: int) -> ActionIrrigation | None: ...

    @abstractmethod
    def ajouter(self, action: ActionIrrigation) -> ActionIrrigation: ...

    @abstractmethod
    def supprimer(self, action: ActionIrrigation) -> None: ...

    @abstractmethod
    def cumul_mm(self, espace_id: int, debut: datetime, fin: datetime) -> float:
        """Somme des apports horodatés dans [debut, fin[ (UTC)."""
