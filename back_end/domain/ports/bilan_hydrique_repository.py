from abc import ABC, abstractmethod
from datetime import date

from domain.models import BilanHydriqueJournalier


class IBilanHydriqueRepository(ABC):
    @abstractmethod
    def save(self, bilan: BilanHydriqueJournalier) -> BilanHydriqueJournalier: ...

    @abstractmethod
    def get_by_espace_and_date(self, espace_id: int, date_bilan: date) -> BilanHydriqueJournalier | None: ...

    @abstractmethod
    def get_dernier_avant(self, espace_id: int, date_bilan: date) -> BilanHydriqueJournalier | None:
        """Dernier bilan strictement antérieur à la date (point de départ du calcul du jour)."""

    @abstractmethod
    def get_dernier_bilan_pour_espace(self, espace_id: int) -> BilanHydriqueJournalier | None: ...

    @abstractmethod
    def get_historique_by_espace(self, espace_id: int, limit: int = 7) -> list[BilanHydriqueJournalier]: ...

    @abstractmethod
    def lister_depuis(self, espace_id: int, date_debut: date) -> list[BilanHydriqueJournalier]:
        """Bilans de l'espace datés de date_debut ou après, par date croissante."""
