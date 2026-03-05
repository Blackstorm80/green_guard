# Fichier : domain/ports/plante_repository.py

from typing import Protocol, Sequence, Optional
from domain.entities import PlanteEntity

class IPlanteRepository(Protocol):
    def lister_toutes(self) -> Sequence[PlanteEntity]:
        """Retourne toutes les plantes du catalogue (pour le GET /plants)."""
        ...

    def get_by_id(self, plante_id: int) -> Optional[PlanteEntity]:
        """Retourne une plante par son id ou None si introuvable."""
        ...

    def sauvegarder(self, plante: PlanteEntity) -> PlanteEntity:
        """Sauvegarde une nouvelle plante ou met à jour une plante existante."""
        ...