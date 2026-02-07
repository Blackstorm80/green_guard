# infrastructure/repositories/espace_vert_repository_impl.py

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from domain.entities.espace_vert import EspaceVertEntity
from domain.ports.espace_vert_repository import IEspaceVertRepository


class EspaceVertRepositoryImpl(IEspaceVertRepository):
    def __init__(self, db_session: Session) -> None:
        self._db = db_session

    def _row_to_entity(self, row) -> EspaceVertEntity:
        """Helper pour mapper une ligne de BDD (objet Row) vers une EspaceVertEntity."""
        return EspaceVertEntity(
            id=row.id,
            nom=row.nom,
            type_espace=row.type_espace,
            localisation=row.localisation,
            plante_id=row.plante_id,
            surface_m2=row.surface_m2,
            exposition_reelle=row.exposition_reelle,
            type_sol=row.type_sol,
            ph_sol=row.ph_sol,
            reserve_utile_max=row.reserve_utile_max,
            coefficient_cultural=row.coefficient_cultural,
            zone=row.zone,
            gerant_id=row.gerant_id,
        )

    def get_by_id(self, espace_id: int) -> Optional[EspaceVertEntity]:
        row = self._db.execute(
            text("SELECT * FROM espaces_verts WHERE id = :id"),
            {"id": espace_id},
        ).first()
        return self._row_to_entity(row) if row else None

    def list_tous(self) -> List[EspaceVertEntity]:
        rows = self._db.execute(text("SELECT * FROM espaces_verts ORDER BY nom")).all()
        return [self._row_to_entity(row) for row in rows]

    def sauvegarder(self, espace: EspaceVertEntity) -> EspaceVertEntity:
        stmt = text("""
            INSERT INTO espaces_verts (
                nom, type_espace, localisation, plante_id, surface_m2,
                exposition_reelle, type_sol, ph_sol, reserve_utile_max,
                coefficient_cultural, zone, gerant_id
            ) VALUES (
                :nom, :type_espace, :localisation, :plante_id, :surface_m2,
                :exposition_reelle, :type_sol, :ph_sol, :reserve_utile_max,
                :coefficient_cultural, :zone, :gerant_id
            ) RETURNING id
            """)
        
        result = self._db.execute(stmt, espace.__dict__)
        new_id = result.scalar_one()
        self._db.commit()

        # Retourne une nouvelle entité avec l'ID généré par la BDD
        return EspaceVertEntity(**{**espace.__dict__, "id": new_id})

    def mettre_a_jour(self, espace: EspaceVertEntity) -> EspaceVertEntity:
        stmt = text("""
            UPDATE espaces_verts
            SET
                nom = :nom,
                type_espace = :type_espace,
                localisation = :localisation,
                plante_id = :plante_id,
                surface_m2 = :surface_m2,
                exposition_reelle = :exposition_reelle,
                type_sol = :type_sol,
                ph_sol = :ph_sol,
                reserve_utile_max = :reserve_utile_max,
                coefficient_cultural = :coefficient_cultural,
                zone = :zone,
                gerant_id = :gerant_id
            WHERE id = :id
            """)
        
        self._db.execute(stmt, espace.__dict__)
        self._db.commit()
        return espace