from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.models import EspaceVert


@dataclass(frozen=True)
class EspaceResume:
    id: int
    nom: str
    latitude: float
    longitude: float


class IEspaceVertRepository(ABC):
    """Port d'accès aux espaces verts (seule interface de référence).

    Le périmètre est toujours l'organisation : tous ses membres partagent le même patrimoine.
    """

    @abstractmethod
    def get_by_id(self, espace_id: int) -> EspaceVert | None: ...

    @abstractmethod
    def get_pour_organisation(self, espace_id: int, organisation_id: int) -> EspaceVert | None:
        """Espace par id, uniquement s'il appartient à l'organisation."""

    @abstractmethod
    def list_par_organisation(self, organisation_id: int) -> list[EspaceVert]: ...

    @abstractmethod
    def list_resume_par_organisation(self, organisation_id: int) -> list["EspaceResume"]:
        """Vue allégée (id, nom, latitude, longitude) pour les écrans de synthèse à fort trafic."""

    @abstractmethod
    def save(self, espace: EspaceVert) -> EspaceVert: ...
