from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from domain.models import BilanHydriqueJournalier


class IBilanHydriqueRepository(ABC):
    @abstractmethod
    def save(self, bilan: BilanHydriqueJournalier) -> BilanHydriqueJournalier: ...

    @abstractmethod
    def get_by_espace_and_date(self, espace_id: int, date_bilan: date) -> Optional[BilanHydriqueJournalier]: ...

    @abstractmethod
    def get_dernier_avant(self, espace_id: int, date_bilan: date) -> Optional[BilanHydriqueJournalier]:
        """Dernier bilan strictement antérieur à la date (point de départ du calcul du jour)."""

    @abstractmethod
    def get_dernier_bilan_pour_espace(self, espace_id: int) -> Optional[BilanHydriqueJournalier]: ...

    @abstractmethod
    def get_historique_by_espace(self, espace_id: int, limit: int = 7) -> List[BilanHydriqueJournalier]: ...
