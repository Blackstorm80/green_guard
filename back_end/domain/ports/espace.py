from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Sequence

from domain.models import EspaceVert


class IEspaceVertRepository(ABC):
    """
    Port du domaine pour accéder et persister les espaces verts.
    """

    @abstractmethod
    def get_by_id(self, espace_id: int) -> Optional[EspaceVert]:
        """
        Retourne un espace vert par son id, ou None s'il n'existe pas.
        """
        ...

    @abstractmethod
    def list_tous(self) -> Sequence[EspaceVert]:
        """
        Retourne tous les espaces verts.
        """
        ...

    @abstractmethod
    def save(self, espace: EspaceVert) -> EspaceVert:
        """
        Crée ou met à jour un espace vert et retourne la version persistée.
        """
        ...
