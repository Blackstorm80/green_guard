from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from domain.models import BilanHydriqueJournalier
from domain.ports.bilan_hydrique_repository import IBilanHydriqueRepository


class BilanHydriqueRepositoryImpl(IBilanHydriqueRepository):
    def __init__(self, db: Session):
        self.db = db

    def _par_espace(self, espace_id: int):
        return self.db.query(BilanHydriqueJournalier).filter(BilanHydriqueJournalier.espace_id == espace_id)

    def save(self, bilan: BilanHydriqueJournalier) -> BilanHydriqueJournalier:
        self.db.add(bilan)
        self.db.commit()
        self.db.refresh(bilan)
        return bilan

    def get_by_espace_and_date(self, espace_id: int, date_bilan: date) -> Optional[BilanHydriqueJournalier]:
        return self._par_espace(espace_id).filter(BilanHydriqueJournalier.date == date_bilan).first()

    def get_dernier_avant(self, espace_id: int, date_bilan: date) -> Optional[BilanHydriqueJournalier]:
        return (
            self._par_espace(espace_id)
            .filter(BilanHydriqueJournalier.date < date_bilan)
            .order_by(BilanHydriqueJournalier.date.desc())
            .first()
        )

    def get_dernier_bilan_pour_espace(self, espace_id: int) -> Optional[BilanHydriqueJournalier]:
        return self._par_espace(espace_id).order_by(BilanHydriqueJournalier.date.desc()).first()

    def get_historique_by_espace(self, espace_id: int, limit: int = 7) -> List[BilanHydriqueJournalier]:
        return self._par_espace(espace_id).order_by(BilanHydriqueJournalier.date.desc()).limit(limit).all()
