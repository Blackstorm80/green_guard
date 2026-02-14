# back_end/infrastructure/repositories/espace_vert_repository_impl.py
from typing import List, Optional
from domain.entities.espace_vert import EspaceVertEntity
from domain.ports.espace_vert_repository import IEspaceVertRepository
from sqlalchemy.orm import Session

class EspaceVertRepositoryImpl(IEspaceVertRepository):
    """
    Implémentation FAKE du repository d'espaces verts pour le développement.
    """
    # Le constructeur accepte `db: Session` pour la compatibilité avec l'injection de dépendances.
    def __init__(self, db: Session):
        self.db = db
        # Les données restent en mémoire pour cette implémentation FAKE.
        self._espaces = [
            EspaceVertEntity(id=1, nom="Parc Central", zone="Nord", ville="Lyon", latitude=45.77, longitude=4.85, sante_percent=95),
            EspaceVertEntity(id=2, nom="Toit Bibliothèque Centrale", zone="Centre", ville="Lyon", latitude=45.76, longitude=4.83, sante_percent=65),
            EspaceVertEntity(id=3, nom="Jardin Suspendu Ouest", zone="Ouest", ville="Villeurbanne", latitude=45.76, longitude=4.88, sante_percent=82),
            EspaceVertEntity(id=4, nom="Mur Mairie Sud", zone="Sud", ville="Lyon", latitude=45.74, longitude=4.85, sante_percent=45),
            EspaceVertEntity(id=5, nom="Patio Interne", zone="Centre", ville="Lyon", latitude=45.76, longitude=4.84, sante_percent=78),
        ]

    def get_by_id(self, espace_id: int) -> Optional[EspaceVertEntity]:
        return next((e for e in self._espaces if e.id == espace_id), None)

    def list_tous(self) -> List[EspaceVertEntity]:
        return self._espaces

    def list_by_user(self, user_id: int) -> List[EspaceVertEntity]:
        # Simule que l'admin (id=1) voit tout, les autres ne voient qu'un sous-ensemble.
        if user_id == 1:
            return self._espaces
        else:
            return [e for e in self._espaces if e.id % 2 != 0] # Espaces impairs