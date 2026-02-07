# Fichier : domain/ports/espace_vert_repository.py

from abc import ABC, abstractmethod

from domain.entities import EspaceVertEntity


class IEspaceVertRepository(ABC):
    """
    Port de persistance pour les espaces verts.
    Le domaine l'utilise pour récupérer ou lister les espaces,
    sans connaître les détails de stockage.
    """

    @abstractmethod
    def get_by_id(self, espace_id: int) -> EspaceVertEntity | None:
        """Récupère un espace vert par son identifiant, ou None s'il n'existe pas."""
        pass

    @abstractmethod
    def list_tous(self) -> list[EspaceVertEntity]:
        """Retourne la liste de tous les espaces verts gérés par le système."""
        pass