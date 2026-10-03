from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from domain.models import EspaceVert

STATUT_SANS_DONNEE = "Sans donnée"


@dataclass(frozen=True)
class LectureCapteur:
    """Dernier état connu d'un espace : mesure brute + bilan hydrique du jour."""
    espace_id: int
    nom: str
    temperature_c: float | None
    humidite_percent: float | None
    humidite_air_percent: float | None
    co2_ppm: float | None
    reserve_eau_mm: float | None
    sante_percent: float | None
    statut: str
    timestamp: datetime | None


class ICapteurService(ABC):
    """Port de lecture de la télémétrie d'un espace vert."""

    @abstractmethod
    def lecture_actuelle(self, espace: EspaceVert) -> LectureCapteur:
        """Toujours une lecture ; champs à None et statut STATUT_SANS_DONNEE si rien n'est mesuré."""

    @abstractmethod
    def lectures_actuelles(self, espaces: Sequence[EspaceVert]) -> list[LectureCapteur]:
        """Lectures de plusieurs espaces, dans l'ordre fourni (implémentation sans N+1 attendue)."""
