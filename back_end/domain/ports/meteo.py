from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime

# Profondeur maximale d'une série passée (limite past_days d'Open-Meteo) : borne du rattrapage
SERIE_JOURS_MAX = 92


class MeteoIndisponibleError(Exception):
    """Le fournisseur météo n'a pas pu répondre (réseau, quota, format)."""


@dataclass(frozen=True)
class ConditionsMeteo:
    city: str
    temperature_c: float
    condition: str
    ensoleillement_fort: bool
    humidite: float | None   # humidité relative de l'air (%)
    pluie_jour_mm: float        # cumul de précipitations du jour (mm)
    et0_jour_mm: float | None = None  # évapotranspiration de référence du jour (mm)
    source: str | None = None  # fournisseur, conservé avec le bilan (traçabilité)


@dataclass(frozen=True)
class MeteoJournaliere:
    """Cumuls d'une journée passée (jour du fuseau métier), pour le rattrapage des bilans manqués."""
    jour: date
    et0_mm: float | None
    pluie_mm: float
    source: str | None = None


class IMeteoService(ABC):
    """Port domaine : conditions météo utiles au pilotage."""

    @abstractmethod
    def recuperer_conditions_actuelles(
        self,
        latitude: float,
        longitude: float,
        maintenant: datetime,
    ) -> ConditionsMeteo:
        """Lève MeteoIndisponibleError si le fournisseur ne répond pas."""

    @abstractmethod
    def recuperer_serie_journaliere(
        self,
        latitude: float,
        longitude: float,
        debut: date,
        fin: date,
    ) -> list[MeteoJournaliere]:
        """ET0 et pluie de chaque jour de [debut, fin] (bornes incluses, 92 jours au plus).

        Lève MeteoIndisponibleError si le fournisseur ne répond pas.
        """
