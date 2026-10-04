"""Moteur hydrique FAO-56 paysager : termes du bilan conservés, réserve utile calculée.

bilans_hydriques : nouvelles colonnes des termes du bilan (ET0, KL, Ks, ETc, pluie, pluie efficace,
arrosage, drainage, épuisement début/fin, TAW, RAW, source météo), NULL pour les bilans existants
(termes inconnus), et version_modele = 'historique-v1' pour eux.

espaces_verts.reserve_utile_max devient une surcharge facultative : NULL signifie « réserve calculée »
(TAW = eau utile de la texture × profondeur racinaire). Données existantes : la valeur 100, défaut
imposé jusqu'ici à tous les espaces (et pré-remplie par le formulaire), passe à NULL ; toute autre
valeur, forcément saisie, est conservée comme surcharge. Le retour arrière remet 100 sur les NULL.
coefficient_cultural (désormais coefficient paysager KL) : défaut 0,8 (gazon) pour les nouveaux espaces,
valeurs existantes inchangées.

Revision ID: 0003_moteur_fao56
Revises: 0002_organisations
Create Date: 2026-10-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_moteur_fao56"
down_revision: Union[str, None] = "0002_organisations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ANCIENNE_RESERVE_PAR_DEFAUT = 100
TERMES = (
    "et0_mm", "kl", "ks", "etc_mm", "pluie_mm", "pluie_efficace_mm", "arrosage_mm", "drainage_mm",
    "epuisement_debut_mm", "epuisement_fin_mm", "taw_mm", "raw_mm",
)


def upgrade() -> None:
    with op.batch_alter_table("bilans_hydriques") as batch:
        for terme in TERMES:
            batch.add_column(sa.Column(terme, sa.Float(), nullable=True))
        # Le défaut serveur remplit les lignes existantes, puis disparaît : le calcul fixe toujours la version
        batch.add_column(sa.Column("version_modele", sa.String(length=40), nullable=False,
                                   server_default="historique-v1"))
        batch.add_column(sa.Column("source_meteo", sa.String(length=40), nullable=True))
    with op.batch_alter_table("bilans_hydriques") as batch:
        batch.alter_column("version_modele", existing_type=sa.String(length=40), existing_nullable=False,
                           server_default=None)

    with op.batch_alter_table("espaces_verts") as batch:
        batch.alter_column("reserve_utile_max", existing_type=sa.Float(), nullable=True, server_default=None)
        batch.alter_column("coefficient_cultural", existing_type=sa.Float(), existing_nullable=False,
                           server_default="0.8")
    op.execute(sa.text("UPDATE espaces_verts SET reserve_utile_max = NULL WHERE reserve_utile_max = :defaut")
               .bindparams(defaut=ANCIENNE_RESERVE_PAR_DEFAUT))


def downgrade() -> None:
    op.execute(sa.text("UPDATE espaces_verts SET reserve_utile_max = :defaut WHERE reserve_utile_max IS NULL")
               .bindparams(defaut=ANCIENNE_RESERVE_PAR_DEFAUT))
    with op.batch_alter_table("espaces_verts") as batch:
        batch.alter_column("coefficient_cultural", existing_type=sa.Float(), existing_nullable=False,
                           server_default="1")
        batch.alter_column("reserve_utile_max", existing_type=sa.Float(), nullable=False, server_default="100")

    with op.batch_alter_table("bilans_hydriques") as batch:
        batch.drop_column("source_meteo")
        batch.drop_column("version_modele")
        for terme in reversed(TERMES):
            batch.drop_column(terme)
