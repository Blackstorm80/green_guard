# back_end/infrastructure/repositories/bilan_hydrique_repository_impl.py

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from domain.models import BilanHydriqueJournalier 
from domain.ports.bilan_hydrique_repository import IBilanHydriqueRepository

class BilanHydriqueRepositoryImpl(IBilanHydriqueRepository):
    def __init__(self, db: Session):
        self.db = db

    def save(self, bilan: BilanHydriqueJournalier) -> BilanHydriqueJournalier:
        self.db.add(bilan)
        self.db.commit()
        self.db.refresh(bilan)
        return bilan

    def get_by_espace_and_date(self, espace_id: int, date_bilan: date) -> Optional[BilanHydriqueJournalier]:
        return self.db.query(BilanHydriqueJournalier).filter(
            BilanHydriqueJournalier.espace_id == espace_id,
            BilanHydriqueJournalier.date_bilan == date_bilan
        ).first()

    def get_historique_by_espace(self, espace_id: int, limit: int = 7) -> List[BilanHydriqueJournalier]:
        return self.db.query(BilanHydriqueJournalier).filter(
            BilanHydriqueJournalier.espace_id == espace_id
        ).order_by(BilanHydriqueJournalier.date_bilan.desc()).limit(limit).all()