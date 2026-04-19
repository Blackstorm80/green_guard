# back_end/infrastructure/repositories/base_repository.py

from typing import Generic, Type, TypeVar, List, Optional
from sqlalchemy.orm import Session
from domain.models import Base

# TypeVar pour représenter le modèle SQLAlchemy
ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Repository de base générique pour les opérations de ecriture , lecture , mise a jour , effacer.
    """

    def __init__(self, db: Session, model: Type[ModelType]):
        """
        Initialise le repository.

        :param db: La session de base de données.
        :param model: Le modèle SQLAlchemy sur lequel opérer.
        """
        self.db = db
        self.model = model

    def get(self, id: int) -> Optional[ModelType]:
        """Récupère un objet par son ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Récupère une liste d'objets."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in) -> ModelType:
        """Crée un nouvel objet."""
        db_obj = self.model(**obj_in.dict())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in) -> ModelType:
        """Met à jour un objet existant."""
        obj_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, id: int) -> ModelType:
        """Supprime un objet par son ID."""
        obj = self.db.query(self.model).get(id)
        self.db.delete(obj)
        self.db.commit()
        return obj
