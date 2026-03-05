from sqlalchemy.orm import Session
from typing import List, Optional
from domain.models import EspaceVert
from domain.ports.espace_vert_repository import IEspaceVertRepository

class EspaceVertRepositoryImpl(IEspaceVertRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, espace_id: int) -> Optional[EspaceVert]:
        return self.db.query(EspaceVert).filter(EspaceVert.id == espace_id).first()

    def save(self, espace: EspaceVert) -> EspaceVert:
        self.db.add(espace)
        self.db.commit()
        self.db.refresh(espace)
        return espace

    def get_all(self) -> List[EspaceVert]:
        return self.db.query(EspaceVert).all()