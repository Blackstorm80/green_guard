# Fichier : domain/ports/meteo_service.py

from abc import ABC, abstractmethod
import datetime
from domain.schemas import DonneesMeteoJournalieres

class IMeteoService(ABC):
    """
    Interface (Port) pour un service fournissant des données météo.
    Le domaine dépend de cette abstraction, pas d'une implémentation concrète.
    """

    @abstractmethod
    def get_donnees_meteo_jour(
        self, latitude: float, longitude: float, date: datetime.date
    ) -> DonneesMeteoJournalieres:
        """
        Récupère les données météo pour un lieu et une date donnés.
        """
        pass
