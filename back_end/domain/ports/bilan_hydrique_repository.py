# Fichier : domain/ports/bilan_hydrique_repository.py

from abc import ABC, abstractmethod

from back_end.domain.entities import BilanHydriqueJournalierEntity


class IBilanHydriqueRepository(ABC):
    """
    Interface (Port) pour le repository gérant la persistance des bilans hydriques.
    Le domaine dépend de cette abstraction pour sauvegarder et récupérer les bilans,
    sans connaître les détails de la base de données.
    """

    @abstractmethod
    def get_dernier_bilan_pour_espace(self, espace_id: int) -> BilanHydriqueJournalierEntity | None:
        """Récupère le dernier bilan hydrique enregistré pour un espace vert donné."""
        pass

    @abstractmethod
    def sauvegarder(self, bilan: BilanHydriqueJournalierEntity) -> None:
        """Sauvegarde un nouveau bilan hydrique journalier."""
        pass