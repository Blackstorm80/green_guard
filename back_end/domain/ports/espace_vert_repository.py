from abc import ABC, abstractmethod
from typing import List, Optional
from domain.models import EspaceVert

class IEspaceVertRepository(ABC):
    @abstractmethod
    def get_by_id(self, espace_id: int) -> Optional[EspaceVert]:
        pass

    @abstractmethod
    def save(self, espace: EspaceVert) -> EspaceVert:
        pass

    @abstractmethod
    def get_all(self) -> List[EspaceVert]:
        pass