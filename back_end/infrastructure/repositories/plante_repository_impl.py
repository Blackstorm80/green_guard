# infrastructure/repositories/plante_repository_impl.py

from typing import Sequence, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from domain.entities import PlanteEntity
from domain.ports.plante_repository import IPlanteRepository


class PlanteRepositoryImpl(IPlanteRepository):
    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def _row_to_entity(self, row) -> PlanteEntity:
        """Helper pour mapper une ligne de BDD (objet Row) vers une PlanteEntity."""
        return PlanteEntity(
            id=row.id,
            nom_scientifique=row.nom_scientifique,
            nom_commun=row.nom_commun,
            type_plante=row.type_plante,
            besoin_eau=row.besoin_eau,
            eau_min_mm_semaine=row.eau_min_mm_semaine,
            eau_max_mm_semaine=row.eau_max_mm_semaine,
            temp_min_confort=row.temp_min_confort,
            temp_max_confort=row.temp_max_confort,
            temp_min_survie=row.temp_min_survie,
            temp_max_survie=row.temp_max_survie,
            exposition=row.exposition,
            type_sol_prefere=row.type_sol_prefere,
            ph_min=row.ph_min,
            ph_max=row.ph_max,
            icone=row.icone,
            description_courte=row.description_courte,
        )

    def list_toutes(self) -> Sequence[PlanteEntity]:
        rows = self._db.execute(text("SELECT * FROM plantes ORDER BY nom_commun")).all()
        return [self._row_to_entity(row) for row in rows]

    def get_by_id(self, plante_id: int) -> Optional[PlanteEntity]:
        row = self._db.execute(
            text("SELECT * FROM plantes WHERE id = :id"),
            {"id": plante_id},
        ).first()
        return self._row_to_entity(row) if row else None

    def sauvegarder(self, plante: PlanteEntity) -> PlanteEntity:
        stmt = text("""
            INSERT INTO plantes (
                nom_scientifique, nom_commun, type_plante, besoin_eau,
                eau_min_mm_semaine, eau_max_mm_semaine, temp_min_confort,
                temp_max_confort, temp_min_survie, temp_max_survie,
                exposition, type_sol_prefere, ph_min, ph_max, icone,
                description_courte
            ) VALUES (
                :nom_scientifique, :nom_commun, :type_plante, :besoin_eau,
                :eau_min_mm_semaine, :eau_max_mm_semaine, :temp_min_confort,
                :temp_max_confort, :temp_min_survie, :temp_max_survie,
                :exposition, :type_sol_prefere, :ph_min, :ph_max, :icone,
                :description_courte
            ) RETURNING id
            """)
        
        result = self._db.execute(stmt, plante.__dict__)
        new_id = result.scalar_one()
        self._db.commit()

        # Retourne une nouvelle entité avec l'ID généré par la BDD
        return PlanteEntity(**{**plante.__dict__, "id": new_id})