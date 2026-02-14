# back_end/domain/ports/espace_vert_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.espace_vert import EspaceVertEntity

class IEspaceVertRepository(ABC):
    
    @abstractmethod
    def get_by_id(self, espace_id: int) -> Optional[EspaceVertEntity]:
        ...

    @abstractmethod
    def list_tous(self) -> List[EspaceVertEntity]:
        ...

    @abstractmethod
    def list_by_user(self, user_id: int) -> List[EspaceVertEntity]:
        """Liste les espaces verts associés à un utilisateur."""
        ...