# back_end/domain/ports/meteo.py
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime


class ConditionsMeteo:
    def __init__(
        self,
        city: str,
        temperature_c: float,
        condition: str,
        ensoleillement_fort: bool,
    ) -> None:
        self.city = city
        self.temperature_c = temperature_c
        self.condition = condition
        self.ensoleillement_fort = ensoleillement_fort


class IMeteoService(ABC):
    """
    Port domaine pour récupérer des infos météo utiles au pilotage :
    température, ensoleillement, vent, etc.
    """

    @abstractmethod
    def recuperer_conditions_actuelles(
        self,
        latitude: float,
        longitude: float,
        maintenant: datetime,
    ) -> ConditionsMeteo:
        ...
