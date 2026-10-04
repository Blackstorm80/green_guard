from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

STATUT_SANS_DONNEE = "Sans donnée"


class EspaceIdentifie(Protocol):
    """Ce que la lecture capteurs exige d'un espace : entité complète ou vue allégée (EspaceResume)."""
    id: int
    nom: str
    latitude: float
    longitude: float


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
    def lecture_actuelle(self, espace: EspaceIdentifie) -> LectureCapteur:
        """Toujours une lecture ; champs à None et statut STATUT_SANS_DONNEE si rien n'est mesuré."""

    @abstractmethod
    def lectures_actuelles(self, espaces: Sequence[EspaceIdentifie]) -> list[LectureCapteur]:
        """Lectures de plusieurs espaces, dans l'ordre fourni (implémentation sans N+1 attendue)."""
