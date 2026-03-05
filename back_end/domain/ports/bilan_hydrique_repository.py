# Fichier : domain/ports/bilan_hydrique_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from domain.models import BilanHydriqueJournalier # <--- L'import corrigé !

class IBilanHydriqueRepository(ABC):
    @abstractmethod
    def save(self, bilan: BilanHydriqueJournalier) -> BilanHydriqueJournalier:
        pass

    @abstractmethod
    def get_by_espace_and_date(self, espace_id: int, date_bilan: date) -> Optional[BilanHydriqueJournalier]:
        pass

    @abstractmethod
    def get_historique_by_espace(self, espace_id: int, limit: int = 7) -> List[BilanHydriqueJournalier]:
        pass