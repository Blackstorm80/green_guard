"""Mode sécheresse VigiEau : source d'eau et date de plantation des espaces, niveau du jour par espace,
registre des arrosages.

- espaces_verts.source_eau (reseau, forage, recuperation, riviere ; défaut reseau) et date_plantation ;
- restrictions_secheresse : niveau VigiEau d'un espace pour un jour (unique par espace et par jour) ;
- interventions : registre figé à la réalisation d'un arrosage (realisee_par, secheresse_niveau,
  secheresse_plage_interdite, secheresse_derogation, secheresse_zone).

Données existantes : les espaces reçoivent la source « reseau » (valeur par défaut) ; les arrosages déjà
réalisés gardent un registre vide, agent compris (niveau et agent inconnus à l'époque : rien n'est inventé,
le créateur d'une intervention n'est pas forcément l'agent qui l'a réalisée). Le retour arrière supprime la table et les colonnes : les interventions sont conservées.

PostgreSQL : la nouvelle table est soumise à la même Row Level Security que les autres tables rattachées
à un espace (migration 0002).

Revision ID: 0006_mode_secheresse
Revises: 0005_prevision_notifications
Create Date: 2026-10-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_mode_secheresse"
down_revision: Union[str, None] = "0005_prevision_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SOURCES_EAU = "source_eau IN ('reseau', 'forage', 'recuperation', 'riviere')"
NIVEAUX = "niveau IN ('aucune', 'vigilance', 'alerte', 'alerte_renforcee', 'crise')"
NIVEAUX_REGISTRE = (
    "secheresse_niveau IN ('aucune', 'vigilance', 'alerte', 'alerte_renforcee', 'crise', 'inconnu')"
)
POLITIQUE = "isolation_organisation"
CONDITION_RLS = (
    "(EXISTS (SELECT 1 FROM espaces_verts e WHERE e.id = restrictions_secheresse.espace_id)) "
    "OR current_setting('app.contourner_rls', true) = 'on'"
)


def upgrade() -> None:
    with op.batch_alter_table("espaces_verts") as batch:
        batch.add_column(sa.Column("source_eau", sa.String(length=20), server_default="reseau", nullable=False))
        batch.add_column(sa.Column("date_plantation", sa.Date(), nullable=True))
        batch.create_check_constraint(op.f("ck_espaces_verts_source_eau"), SOURCES_EAU)

    op.create_table(
        "restrictions_secheresse",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("espace_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("niveau", sa.String(length=20), nullable=False),
        sa.Column("type_zone", sa.String(length=3), nullable=True),
        sa.Column("zone_nom", sa.String(length=255), nullable=True),
        sa.Column("zone_code", sa.String(length=60), nullable=True),
        sa.Column("arrete_identifiant", sa.String(length=40), nullable=True),
        sa.Column("arrete_url", sa.String(length=500), nullable=True),
        sa.Column("recupere_le", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(NIVEAUX, name=op.f("ck_restrictions_secheresse_niveau")),
        sa.ForeignKeyConstraint(["espace_id"], ["espaces_verts.id"],
                                name=op.f("fk_restrictions_secheresse_espace_id_espaces_verts"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_restrictions_secheresse")),
        sa.UniqueConstraint("espace_id", "date", name="uq_restrictions_secheresse_espace_date"),
    )
    op.create_index(op.f("ix_restrictions_secheresse_id"), "restrictions_secheresse", ["id"], unique=False)
    op.create_index(op.f("ix_restrictions_secheresse_espace_id"), "restrictions_secheresse", ["espace_id"],
                    unique=False)

    with op.batch_alter_table("interventions") as batch:
        batch.add_column(sa.Column("realisee_par", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("secheresse_niveau", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("secheresse_plage_interdite", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("secheresse_derogation", sa.String(length=200), nullable=True))
        batch.add_column(sa.Column("secheresse_zone", sa.String(length=255), nullable=True))
        batch.create_check_constraint(op.f("ck_interventions_secheresse_niveau"), NIVEAUX_REGISTRE)
        batch.create_foreign_key(op.f("fk_interventions_realisee_par_users"), "users", ["realisee_par"], ["id"],
                                 ondelete="SET NULL")

    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE restrictions_secheresse ENABLE ROW LEVEL SECURITY")
        op.execute("ALTER TABLE restrictions_secheresse FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY {POLITIQUE} ON restrictions_secheresse USING ({CONDITION_RLS}) "
                   f"WITH CHECK ({CONDITION_RLS})")


def downgrade() -> None:
    with op.batch_alter_table("interventions") as batch:
        batch.drop_constraint(op.f("fk_interventions_realisee_par_users"), type_="foreignkey")
        batch.drop_constraint(op.f("ck_interventions_secheresse_niveau"), type_="check")
        batch.drop_column("secheresse_zone")
        batch.drop_column("secheresse_derogation")
        batch.drop_column("secheresse_plage_interdite")
        batch.drop_column("secheresse_niveau")
        batch.drop_column("realisee_par")

    # La politique RLS disparaît avec la table
    op.drop_index(op.f("ix_restrictions_secheresse_espace_id"), table_name="restrictions_secheresse")
    op.drop_index(op.f("ix_restrictions_secheresse_id"), table_name="restrictions_secheresse")
    op.drop_table("restrictions_secheresse")

    with op.batch_alter_table("espaces_verts") as batch:
        batch.drop_constraint(op.f("ck_espaces_verts_source_eau"), type_="check")
        batch.drop_column("date_plantation")
        batch.drop_column("source_eau")
