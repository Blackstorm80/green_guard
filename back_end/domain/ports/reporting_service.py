# Fichier : domain/ports/reporting_service.py

from abc import ABC, abstractmethod
from typing import List

from back_end.domain.entities import BilanHydriqueJournalierEntity


class IReportingService(ABC):
    """
    Interface (Port) pour un service de génération de rapports.
    """

    @abstractmethod
    def generer_rapport_bilan_hydrique(self, nom_espace: str, bilans: List[BilanHydriqueJournalierEntity]) -> str:
        """
        Génère un rapport à partir d'une liste de bilans hydriques.
        Le format de sortie (CSV, texte, etc.) est défini par l'implémentation.
        """
        pass