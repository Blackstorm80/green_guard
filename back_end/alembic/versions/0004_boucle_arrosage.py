"""Boucle arrosage vers le bilan : un arrosage terminé crée l'apport d'eau compté dans le bilan.

actions_irrigation.intervention_id (unique, ON DELETE CASCADE) relie l'apport à l'intervention
d'arrosage qui l'a produit : jamais deux apports pour une même intervention.
espaces_verts.debit_arrosage_l_min (facultatif) convertit la dose recommandée en minutes.

Données existantes : les interventions d'arrosage déjà terminées avec un volume (jamais comptées
jusqu'ici) reçoivent leur apport (volume / surface, horodaté à la réalisation, sinon à la création),
si la surface de l'espace est connue. Les bilans passés ne sont pas recalculés ; un apport du jour
est pris en compte au prochain passage du worker. Le retour arrière supprime ces apports liés
(dérivés des interventions, recréés par la migration montante) puis les colonnes.

Revision ID: 0004_boucle_arrosage
Revises: 0003_moteur_fao56
Create Date: 2026-10-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_boucle_arrosage"
down_revision: Union[str, None] = "0003_moteur_fao56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("espaces_verts") as batch:
        batch.add_column(sa.Column("debit_arrosage_l_min", sa.Float(), nullable=True))

    with op.batch_alter_table("actions_irrigation") as batch:
        batch.add_column(sa.Column("intervention_id", sa.Integer(), nullable=True))
        batch.create_unique_constraint(op.f("uq_actions_irrigation_intervention_id"), ["intervention_id"])
        batch.create_foreign_key(
            op.f("fk_actions_irrigation_intervention_id_interventions"), "interventions",
            ["intervention_id"], ["id"], ondelete="CASCADE",
        )

    op.execute(sa.text(
        "INSERT INTO actions_irrigation (espace_id, quantite_mm, timestamp, intervention_id) "
        "SELECT i.espace_id, i.volume_eau_l / e.surface_m2, COALESCE(i.realisee_le, i.cree_le), i.id "
        "FROM interventions i JOIN espaces_verts e ON e.id = i.espace_id "
        "WHERE i.type = 'arrosage' AND i.statut = 'terminee' AND i.volume_eau_l > 0 AND e.surface_m2 > 0"
    ))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM actions_irrigation WHERE intervention_id IS NOT NULL"))
    with op.batch_alter_table("actions_irrigation") as batch:
        batch.drop_constraint(op.f("fk_actions_irrigation_intervention_id_interventions"), type_="foreignkey")
        batch.drop_constraint(op.f("uq_actions_irrigation_intervention_id"), type_="unique")
        batch.drop_column("intervention_id")

    with op.batch_alter_table("espaces_verts") as batch:
        batch.drop_column("debit_arrosage_l_min")
