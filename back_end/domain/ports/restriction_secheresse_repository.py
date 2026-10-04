from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime

from domain.models import RestrictionSecheresse
from domain.ports.vigieau import NiveauVigieau


class IRestrictionSecheresseRepository(ABC):
    """Niveaux VigiEau relevés par espace et par jour. Les écritures ne valident pas la transaction."""

    @abstractmethod
    def get(self, espace_id: int, jour: date) -> RestrictionSecheresse | None: ...

    @abstractmethod
    def plus_proche(self, espace_id: int, jour: date, fenetre_jours: int) -> RestrictionSecheresse | None:
        """Relevé de l'espace le plus proche de `jour` à `fenetre_jours` près ; à égale distance, le plus
        sévère. None si aucun."""

    @abstractmethod
    def par_espaces(self, espace_ids: Iterable[int], jour: date) -> dict[int, RestrictionSecheresse]: ...

    @abstractmethod
    def en_vigueur(self, espace_ids: Iterable[int], jour: date,
                   fenetre_jours: int) -> dict[int, RestrictionSecheresse]:
        """Dernier relevé de chaque espace daté de `jour` ou des `fenetre_jours` jours précédents."""

    @abstractmethod
    def enregistrer(self, espace_id: int, jour: date, niveau: NiveauVigieau,
                    maintenant: datetime) -> RestrictionSecheresse:
        """Crée ou remplace le relevé du jour de l'espace, sans erreur si une écriture concurrente
        l'a créé entre-temps."""


@dataclass(frozen=True)
class LigneRegistre:
    """Arrosage réalisé, tel que figé dans le registre sécheresse."""
    realisee_le: datetime
    espace: str
    commune: str | None
    volume_l: float | None
    niveau: str | None
    plage_interdite: str | None
    derogation: str | None
    zone: str | None
    agent: str | None        # None : compte de l'agent supprimé


class IRegistreSecheresseRepository(ABC):
    @abstractmethod
    def lister(self, organisation_id: int, debut: datetime, fin: datetime) -> list[LigneRegistre]:
        """Arrosages terminés de l'organisation réalisés dans [debut, fin[ (UTC), par date croissante."""
