# back_end/infrastructure/repositories/bilan_hydrique_repository_impl.py

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from domain.entities import BilanHydriqueJournalierEntity
from domain.ports.bilan_hydrique_repository import IBilanHydriqueRepository

class BilanHydriqueRepositoryImpl(IBilanHydriqueRepository):
    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def _row_to_entity(self, row) -> BilanHydriqueJournalierEntity:
        return BilanHydriqueJournalierEntity(
            id=row.id,
            date=row.date_bilan, # Attention au nom de colonne en DB
            reserve_eau=row.reserve_eau,
            indice_stress=row.indice_stress,
            statut_hydrique=row.statut_hydrique,
            stress_sanitaire=row.stress_sanitaire,
            espace_id=row.espace_id,
            co2_absorbe_jour=row.co2_absorbe_jour,
            o2_produit_jour=row.o2_produit_jour
        )

    def get_dernier_bilan_pour_espace(self, espace_id: int) -> Optional[BilanHydriqueJournalierEntity]:
        # On suppose une table 'bilans_hydriques'
        stmt = text("""
            SELECT * FROM bilans_hydriques 
            WHERE espace_id = :eid 
            ORDER BY date_bilan DESC 
            LIMIT 1
        """)
        row = self._db.execute(stmt, {"eid": espace_id}).first()
        return self._row_to_entity(row) if row else None

    def sauvegarder(self, bilan: BilanHydriqueJournalierEntity) -> None:
        # Implémentation simplifiée pour l'exemple
        stmt = text("""
            INSERT INTO bilans_hydriques (date_bilan, reserve_eau, indice_stress, statut_hydrique, stress_sanitaire, espace_id, co2_absorbe_jour, o2_produit_jour)
            VALUES (:date, :reserve_eau, :indice_stress, :statut_hydrique, :stress_sanitaire, :espace_id, :co2, :o2)
        """)
        params = bilan.__dict__.copy()
        params['co2'] = bilan.co2_absorbe_jour
        params['o2'] = bilan.o2_produit_jour
        self._db.execute(stmt, params)
        self._db.commit()
