from abc import ABC, abstractmethod
from typing import List, Optional

from domain.models import EspaceVert


class IEspaceVertRepository(ABC):
    """Port d'accès aux espaces verts (seule interface de référence)."""

    @abstractmethod
    def get_by_id(self, espace_id: int) -> Optional[EspaceVert]: ...

    @abstractmethod
    def get_for_user(self, espace_id: int, user_id: int) -> Optional[EspaceVert]:
        """Espace par id, uniquement s'il appartient à l'utilisateur."""

    @abstractmethod
    def list_by_user(self, user_id: int) -> List[EspaceVert]: ...

    @abstractmethod
    def list_tous(self) -> List[EspaceVert]: ...

    @abstractmethod
    def save(self, espace: EspaceVert) -> EspaceVert: ...
