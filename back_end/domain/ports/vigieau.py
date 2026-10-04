from abc import ABC, abstractmethod
from dataclasses import dataclass


class VigieauIndisponibleError(Exception):
    """VigiEau n'a pas pu donner le niveau d'un point (réponse en erreur ou inexploitable)."""


class VigieauInjoignableError(VigieauIndisponibleError):
    """Panne générale (réseau, délai dépassé) : inutile d'interroger les points suivants."""


@dataclass(frozen=True)
class NiveauVigieau:
    """Zone d'alerte retenue pour un point ; niveau « aucune » si aucune zone n'est en vigueur."""
    niveau: str
    type_zone: str | None = None
    zone_nom: str | None = None
    zone_code: str | None = None
    arrete_identifiant: str | None = None
    arrete_url: str | None = None


class IVigieauService(ABC):
    @abstractmethod
    def niveau_au_point(self, latitude: float, longitude: float, type_zone: str | None) -> NiveauVigieau:
        """type_zone : AEP, SOU ou SUP ; None : zone la plus sévère tous types confondus.

        Lève VigieauIndisponibleError (ou VigieauInjoignableError).
        """
