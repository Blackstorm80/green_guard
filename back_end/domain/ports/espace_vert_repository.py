from abc import ABC, abstractmethod

from domain.models import EspaceVert


class IEspaceVertRepository(ABC):
    """Port d'accès aux espaces verts (seule interface de référence)."""

    @abstractmethod
    def get_by_id(self, espace_id: int) -> EspaceVert | None: ...

    @abstractmethod
    def get_for_user(self, espace_id: int, user_id: int) -> EspaceVert | None:
        """Espace par id, uniquement s'il appartient à l'utilisateur."""

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[EspaceVert]: ...

    @abstractmethod
    def list_tous(self) -> list[EspaceVert]: ...

    @abstractmethod
    def save(self, espace: EspaceVert) -> EspaceVert: ...
