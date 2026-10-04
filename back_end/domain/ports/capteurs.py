from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from domain.logic.arrosage import DoseRecommandee

STATUT_SANS_DONNEE = "Sans donnée"


class EspaceIdentifie(Protocol):
    """Ce que la lecture capteurs exige d'un espace : entité complète ou vue allégée (EspaceResume).

    surface_m2, type_irrigation et debit_arrosage_l_min, lus s'ils existent, chiffrent la dose recommandée.
    """
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
    # Termes du dernier bilan FAO-56 (None pour un bilan antérieur au modèle)
    reserve_max_mm: float | None = None
    reserve_facilement_utilisable_mm: float | None = None
    reserve_percent: float | None = None
    et0_mm: float | None = None
    etc_mm: float | None = None
    date_bilan: date | None = None
    version_modele: str | None = None
    # Dose pour revenir à la capacité au champ (bilan FAO-56 seulement)
    dose_recommandee: DoseRecommandee | None = None


class ICapteurService(ABC):
    """Port de lecture de la télémétrie d'un espace vert."""

    @abstractmethod
    def lecture_actuelle(self, espace: EspaceIdentifie) -> LectureCapteur:
        """Toujours une lecture ; champs à None et statut STATUT_SANS_DONNEE si rien n'est mesuré."""

    @abstractmethod
    def lectures_actuelles(self, espaces: Sequence[EspaceIdentifie]) -> list[LectureCapteur]:
        """Lectures de plusieurs espaces, dans l'ordre fourni (implémentation sans N+1 attendue)."""
