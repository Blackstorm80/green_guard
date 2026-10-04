"""Prévision à 7 jours : les alertes du worker sont rattachées à leur espace.

notifications.espace_id (facultatif, ON DELETE SET NULL) : une alerte « Arrosage à prévoir » n'est
émise qu'une fois par espace et par jour, quel que soit le texte (la date limite peut changer dans
la journée), et l'historique des notifications survit à la suppression de l'espace.

Données existantes : les alertes de stress critique déjà émises sont rattachées à leur espace quand
leur message désigne sans ambiguïté un espace de l'organisation du destinataire (sinon, laissées
sans espace). Le retour arrière supprime seulement la colonne : aucune notification n'est perdue.

Revision ID: 0005_prevision_notifications
Revises: 0004_boucle_arrosage
Create Date: 2026-10-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_prevision_notifications"
down_revision: Union[str, None] = "0004_boucle_arrosage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Message des alertes de stress critique (infrastructure/jobs/mise_a_jour_capteurs.py)
ESPACE_DU_MESSAGE = (
    "FROM espaces_verts e JOIN users u ON u.organisation_id = e.organisation_id "
    "WHERE u.id = notifications.user_id "
    "AND notifications.message = 'Stress hydrique critique sur « ' || e.nom || ' » : arrosage recommandé.'"
)


def upgrade() -> None:
    with op.batch_alter_table("notifications") as batch:
        batch.add_column(sa.Column("espace_id", sa.Integer(), nullable=True))
        batch.create_index(op.f("ix_notifications_espace_id"), ["espace_id"], unique=False)
        batch.create_foreign_key(
            op.f("fk_notifications_espace_id_espaces_verts"), "espaces_verts",
            ["espace_id"], ["id"], ondelete="SET NULL",
        )

    op.execute(sa.text(
        f"UPDATE notifications SET espace_id = (SELECT MIN(e.id) {ESPACE_DU_MESSAGE}) "
        f"WHERE type = 'stress_hydrique' AND (SELECT COUNT(*) {ESPACE_DU_MESSAGE}) = 1"
    ))


def downgrade() -> None:
    with op.batch_alter_table("notifications") as batch:
        batch.drop_constraint(op.f("fk_notifications_espace_id_espaces_verts"), type_="foreignkey")
        batch.drop_index(op.f("ix_notifications_espace_id"))
        batch.drop_column("espace_id")
