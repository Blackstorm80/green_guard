from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class MeteoIndisponibleError(Exception):
    """Le fournisseur météo n'a pas pu répondre (réseau, quota, format)."""


@dataclass(frozen=True)
class ConditionsMeteo:
    city: str
    temperature_c: float
    condition: str
    ensoleillement_fort: bool
    humidite: Optional[float]   # humidité relative de l'air (%)
    pluie_jour_mm: float        # cumul de précipitations du jour (mm)
    et0_jour_mm: Optional[float] = None  # évapotranspiration de référence du jour (mm)


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
