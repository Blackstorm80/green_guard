from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.logic.droits import ADMIN
from domain.models import Organisation, User
from domain.ports.organisation_repository import IOrganisationRepository


class OrganisationRepositoryImpl(IOrganisationRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self, organisation_id: int) -> Organisation | None:
        return self.db.get(Organisation, organisation_id)

    def get_par_slug(self, slug: str) -> Organisation | None:
        return self.db.query(Organisation).filter(Organisation.slug == slug).first()

    def slug_existe(self, slug: str) -> bool:
        return self.db.query(Organisation.id).filter(Organisation.slug == slug).first() is not None

    def email_existe(self, email: str) -> bool:
        return self.db.query(User.id).filter(func.lower(User.email) == email.lower()).first() is not None

    def lister_membres(self, organisation_id: int) -> list[User]:
        return self.db.query(User).filter(User.organisation_id == organisation_id).order_by(User.name, User.id).all()

    def get_membre(self, organisation_id: int, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id, User.organisation_id == organisation_id).first()

    def compter_admins_actifs(self, organisation_id: int) -> int:
        return (
            self.db.query(func.count(User.id))
            .filter(User.organisation_id == organisation_id, User.role == ADMIN, User.is_active.is_(True))
            .scalar()
        )

    def ajouter(self, objet: Organisation | User) -> None:
        self.db.add(objet)
        self.db.flush()

    def valider(self) -> None:
        self.db.commit()
