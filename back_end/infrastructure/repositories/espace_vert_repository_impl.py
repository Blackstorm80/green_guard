from sqlalchemy.orm import Session

from domain.models import EspaceVert
from domain.ports.espace_vert_repository import IEspaceVertRepository


class EspaceVertRepositoryImpl(IEspaceVertRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, espace_id: int) -> EspaceVert | None:
        return self.db.get(EspaceVert, espace_id)

    def get_for_user(self, espace_id: int, user_id: int) -> EspaceVert | None:
        return (
            self.db.query(EspaceVert)
            .filter(EspaceVert.id == espace_id, EspaceVert.user_id == user_id)
            .first()
        )

    def list_by_user(self, user_id: int) -> list[EspaceVert]:
        return self.db.query(EspaceVert).filter(EspaceVert.user_id == user_id).order_by(EspaceVert.id).all()

    def list_tous(self) -> list[EspaceVert]:
        return self.db.query(EspaceVert).order_by(EspaceVert.id).all()

    def save(self, espace: EspaceVert) -> EspaceVert:
        self.db.add(espace)
        self.db.commit()
        self.db.refresh(espace)
        return espace
