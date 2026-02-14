from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Sequence

from domain.entities import EspaceVertEntity


class IEspaceVertRepository(ABC):
    """
    Port du domaine pour accéder et persister les espaces verts.
    """

    @abstractmethod
    def get_by_id(self, espace_id: int) -> Optional[EspaceVertEntity]:
        """
        Retourne un espace vert par son id, ou None s'il n'existe pas.
        """
        ...

    @abstractmethod
    def list_tous(self) -> Sequence[EspaceVertEntity]:
        """
        Retourne tous les espaces verts.
        """
        ...

    @abstractmethod
    def save(self, espace: EspaceVertEntity) -> EspaceVertEntity:
        """
        Crée ou met à jour un espace vert et retourne la version persistée.
        """
        ...
