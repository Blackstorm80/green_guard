# Fichier : tests/mocks/mock_meteo_service.py

import datetime
from domain.ports.meteo_service import IMeteoService
from domain.schemas import DonneesMeteoJournalieres

class FakeMeteoService(IMeteoService):
    """
    Un faux service météo pour les tests. Il retourne des données prévisibles
    sans appeler une véritable API.
    """
    def __init__(self, pluie_mm: float, et0_mm: float):
        self.pluie_mm = pluie_mm
        self.et0_mm = et0_mm

    def get_donnees_meteo_jour(
        self, latitude: float, longitude: float, date: datetime.date
    ) -> DonneesMeteoJournalieres:
        # Ignore lat, lon, et date, et retourne les valeurs configurées
        return DonneesMeteoJournalieres(
            date=date, pluie_mm=self.pluie_mm, et0_mm=self.et0_mm
        )
