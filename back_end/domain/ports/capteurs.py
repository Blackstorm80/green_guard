from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from domain.models import EspaceVert

STATUT_SANS_DONNEE = "Sans donnée"


@dataclass(frozen=True)
class LectureCapteur:
    """Dernier état connu d'un espace : mesure brute + bilan hydrique du jour."""
    espace_id: int
    nom: str
    temperature_c: Optional[float]
    humidite_percent: Optional[float]
    humidite_air_percent: Optional[float]
    co2_ppm: Optional[float]
    reserve_eau_mm: Optional[float]
    sante_percent: Optional[float]
    statut: str
    timestamp: Optional[datetime]


class ICapteurService(ABC):
    """Port de lecture de la télémétrie d'un espace vert."""

    @abstractmethod
    def lecture_actuelle(self, espace: EspaceVert) -> LectureCapteur:
        """Toujours une lecture ; champs à None et statut STATUT_SANS_DONNEE si rien n'est mesuré."""
