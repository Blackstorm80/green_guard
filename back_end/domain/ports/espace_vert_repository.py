# Fichier : domain/ports/espace_vert_repository.py

from typing import Protocol

from domain.entities.espace_vert import EspaceVertEntity


class IEspaceVertRepository(Protocol):
    """
    Port de persistance pour les espaces verts.
    Le domaine l'utilise pour récupérer ou lister les espaces,
    sans connaître les détails de stockage.
    """

    def get_by_id(self, espace_id: int) -> EspaceVertEntity | None:
        """Récupère un espace vert par son identifiant, ou None s'il n'existe pas."""
        ...

    def list_tous(self) -> list[EspaceVertEntity]:
        """Retourne la liste de tous les espaces verts gérés par le système."""
        ...

    def sauvegarder(self, espace: EspaceVertEntity) -> EspaceVertEntity:
        """Crée un nouvel espace vert."""
        ...

    def mettre_a_jour(self, espace: EspaceVertEntity) -> EspaceVertEntity:
        """Met à jour un espace vert existant."""
        ...