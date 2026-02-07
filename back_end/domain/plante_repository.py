# Fichier : domain/ports/plante_repository.py

from typing import Protocol, List
from domain.entities.plante import PlanteEntity

class IPlanteRepository(Protocol):
    def lister_toutes(self) -> List[PlanteEntity]:
        """Retourne toutes les plantes du catalogue."""
        ...

    def sauvegarder(self, plante: PlanteEntity) -> PlanteEntity:
        """Sauvegarde une nouvelle plante ou met à jour une plante existante."""
        ...