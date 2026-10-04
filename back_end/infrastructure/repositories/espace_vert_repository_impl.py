from sqlalchemy.orm import Session, selectinload

from domain.models import EspaceVert
from domain.ports.espace_vert_repository import EspaceResume, IEspaceVertRepository


class EspaceVertRepositoryImpl(IEspaceVertRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, espace_id: int) -> EspaceVert | None:
        return self.db.get(EspaceVert, espace_id)

    def get_pour_organisation(self, espace_id: int, organisation_id: int) -> EspaceVert | None:
        return (
            self.db.query(EspaceVert)
            .filter(EspaceVert.id == espace_id, EspaceVert.organisation_id == organisation_id)
            .first()
        )

    def list_par_organisation(self, organisation_id: int) -> list[EspaceVert]:
        # Zones chargées en une requête : EspaceVertRead expose zone_id (sinon une requête par espace)
        return (
            self.db.query(EspaceVert)
            .options(selectinload(EspaceVert.zones))
            .filter(EspaceVert.organisation_id == organisation_id)
            .order_by(EspaceVert.id)
            .all()
        )

    def list_resume_par_organisation(self, organisation_id: int) -> list[EspaceResume]:
        lignes = (
            self.db.query(EspaceVert.id, EspaceVert.nom, EspaceVert.latitude, EspaceVert.longitude,
                          EspaceVert.surface_m2, EspaceVert.type_irrigation, EspaceVert.debit_arrosage_l_min,
                          EspaceVert.source_eau, EspaceVert.date_plantation, EspaceVert.type_espace)
            .filter(EspaceVert.organisation_id == organisation_id)
            .order_by(EspaceVert.id)
        )
        return [EspaceResume(*ligne) for ligne in lignes]

    def save(self, espace: EspaceVert) -> EspaceVert:
        self.db.add(espace)
        self.db.commit()
        self.db.refresh(espace)
        return espace
