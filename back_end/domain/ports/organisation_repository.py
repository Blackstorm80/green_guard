from abc import ABC, abstractmethod

from domain.models import Organisation, User


class IOrganisationRepository(ABC):
    """Port d'accès aux organisations et à leurs membres."""

    @abstractmethod
    def get(self, organisation_id: int) -> Organisation | None: ...

    @abstractmethod
    def get_par_slug(self, slug: str) -> Organisation | None: ...

    @abstractmethod
    def slug_existe(self, slug: str) -> bool: ...

    @abstractmethod
    def email_existe(self, email: str) -> bool:
        """Recherche sur toute l'instance : l'e-mail identifie un compte de façon unique."""

    @abstractmethod
    def lister_membres(self, organisation_id: int) -> list[User]: ...

    @abstractmethod
    def get_membre(self, organisation_id: int, user_id: int) -> User | None: ...

    @abstractmethod
    def compter_admins_actifs(self, organisation_id: int) -> int: ...

    @abstractmethod
    def ajouter(self, objet: Organisation | User) -> None:
        """Ajoute à la transaction en cours (identifiant attribué), sans valider."""

    @abstractmethod
    def valider(self) -> None: ...
