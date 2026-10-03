"""Schéma v1 : contraintes d'intégrité, cascades, index et dates avec fuseau horaire.

Remplace la migration initiale ab36bd25cc59 (clés étrangères non nommées, non modifiables
de façon portable). Projet sans données de production : une base de développement créée
avec l'ancienne migration doit être recréée (docker compose down -v).

Revision ID: 0001_schema_v1
Revises:
Create Date: 2026-10-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_schema_v1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('auxiliaires',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('role', sa.String(), nullable=True),
    sa.Column('url_image', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_auxiliaires'))
    )
    op.create_index(op.f('ix_auxiliaires_id'), 'auxiliaires', ['id'], unique=False)
    op.create_index(op.f('ix_auxiliaires_nom'), 'auxiliaires', ['nom'], unique=False)
    op.create_table('especes_vegetales',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom_scientifique', sa.String(), nullable=True),
    sa.Column('nom_commun', sa.String(), nullable=True),
    sa.Column('famille', sa.String(), nullable=True),
    sa.Column('temperature_min', sa.Float(), nullable=True),
    sa.Column('temperature_max', sa.Float(), nullable=True),
    sa.Column('humidite_min', sa.Float(), nullable=True),
    sa.Column('humidite_max', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_especes_vegetales'))
    )
    op.create_index(op.f('ix_especes_vegetales_id'), 'especes_vegetales', ['id'], unique=False)
    op.create_index(op.f('ix_especes_vegetales_nom_scientifique'), 'especes_vegetales', ['nom_scientifique'], unique=False)
    op.create_table('niveaux_alertes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('libelle', sa.String(), nullable=True),
    sa.Column('priorite', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_niveaux_alertes'))
    )
    op.create_index(op.f('ix_niveaux_alertes_code'), 'niveaux_alertes', ['code'], unique=True)
    op.create_index(op.f('ix_niveaux_alertes_id'), 'niveaux_alertes', ['id'], unique=False)
    op.create_table('plantes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom_scientifique', sa.String(), nullable=True),
    sa.Column('nom_commun', sa.String(), nullable=True),
    sa.Column('famille', sa.String(), nullable=True),
    sa.Column('ph_ideal', sa.Float(), nullable=True),
    sa.Column('besoin_eau', sa.String(), nullable=True),
    sa.Column('url_image', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_plantes'))
    )
    op.create_index(op.f('ix_plantes_id'), 'plantes', ['id'], unique=False)
    op.create_index(op.f('ix_plantes_nom_scientifique'), 'plantes', ['nom_scientifique'], unique=False)
    op.create_table('types_alertes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('libelle', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_types_alertes'))
    )
    op.create_index(op.f('ix_types_alertes_code'), 'types_alertes', ['code'], unique=True)
    op.create_index(op.f('ix_types_alertes_id'), 'types_alertes', ['id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('role', sa.String(), server_default='user', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.CheckConstraint("role IN ('admin', 'manager', 'user')", name=op.f('ck_users_role')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('clustering_configs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom_config', sa.String(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('n_clusters', sa.Integer(), server_default='5', nullable=False),
    sa.Column('distance_max', sa.Float(), nullable=True),
    sa.Column('algorithme', sa.String(), nullable=True),
    sa.Column('granularite', sa.String(), nullable=True),
    sa.Column('rayon_max_km', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_clustering_configs_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_clustering_configs')),
    sa.UniqueConstraint('nom_config', name=op.f('uq_clustering_configs_nom_config'))
    )
    op.create_index(op.f('ix_clustering_configs_id'), 'clustering_configs', ['id'], unique=False)
    op.create_index(op.f('ix_clustering_configs_user_id'), 'clustering_configs', ['user_id'], unique=False)
    op.create_table('espaces_verts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(), nullable=False),
    sa.Column('ville', sa.String(), nullable=True),
    sa.Column('zone', sa.String(), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=False),
    sa.Column('longitude', sa.Float(), nullable=False),
    sa.Column('surface_m2', sa.Float(), nullable=True),
    sa.Column('type_espace', sa.String(), server_default='Jardin', nullable=False),
    sa.Column('type_sol', sa.String(), nullable=True),
    sa.Column('ph_actuel', sa.Float(), nullable=True),
    sa.Column('exposition', sa.String(), nullable=True),
    sa.Column('drainage', sa.String(), nullable=True),
    sa.Column('humidite_cible', sa.Float(), nullable=True),
    sa.Column('frequence_arrosage_auto', sa.Integer(), nullable=True),
    sa.Column('profondeur_racinaire', sa.Float(), nullable=True),
    sa.Column('type_irrigation', sa.String(), nullable=True),
    sa.Column('date_derniere_fertilisation', sa.Date(), nullable=True),
    sa.Column('sante_percent', sa.Float(), nullable=True),
    sa.Column('reserve_utile_max', sa.Float(), server_default='100', nullable=False),
    sa.Column('coefficient_cultural', sa.Float(), server_default='1', nullable=False),
    sa.Column('cree_le', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_espaces_verts_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_espaces_verts'))
    )
    op.create_index(op.f('ix_espaces_verts_id'), 'espaces_verts', ['id'], unique=False)
    op.create_index(op.f('ix_espaces_verts_user_id'), 'espaces_verts', ['user_id'], unique=False)
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('type', sa.String(), server_default='info', nullable=False),
    sa.Column('est_lue', sa.Boolean(), server_default=sa.false(), nullable=False),
    sa.Column('cree_le', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_notifications_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notifications'))
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_table('zones_intelligentes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('granularite', sa.String(), nullable=True),
    sa.Column('centroid_lat', sa.Float(), nullable=True),
    sa.Column('centroid_lon', sa.Float(), nullable=True),
    sa.Column('rayon_km', sa.Float(), nullable=True),
    sa.Column('sante_moyenne', sa.Float(), nullable=True),
    sa.Column('nb_espaces', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_zones_intelligentes_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_zones_intelligentes'))
    )
    op.create_index(op.f('ix_zones_intelligentes_id'), 'zones_intelligentes', ['id'], unique=False)
    op.create_index(op.f('ix_zones_intelligentes_user_id'), 'zones_intelligentes', ['user_id'], unique=False)
    op.create_table('actions_irrigation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('espace_id', sa.Integer(), nullable=False),
    sa.Column('quantite_mm', sa.Float(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['espace_id'], ['espaces_verts.id'], name=op.f('fk_actions_irrigation_espace_id_espaces_verts'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_actions_irrigation'))
    )
    op.create_index(op.f('ix_actions_irrigation_espace_id'), 'actions_irrigation', ['espace_id'], unique=False)
    op.create_index(op.f('ix_actions_irrigation_id'), 'actions_irrigation', ['id'], unique=False)
    op.create_table('alertes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('espace_id', sa.Integer(), nullable=True),
    sa.Column('type_alerte_id', sa.Integer(), nullable=True),
    sa.Column('niveau_alerte_id', sa.Integer(), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('est_resolue', sa.Boolean(), nullable=True),
    sa.Column('cree_le', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    sa.ForeignKeyConstraint(['espace_id'], ['espaces_verts.id'], name=op.f('fk_alertes_espace_id_espaces_verts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['niveau_alerte_id'], ['niveaux_alertes.id'], name=op.f('fk_alertes_niveau_alerte_id_niveaux_alertes')),
    sa.ForeignKeyConstraint(['type_alerte_id'], ['types_alertes.id'], name=op.f('fk_alertes_type_alerte_id_types_alertes')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_alertes'))
    )
    op.create_index(op.f('ix_alertes_espace_id'), 'alertes', ['espace_id'], unique=False)
    op.create_index(op.f('ix_alertes_id'), 'alertes', ['id'], unique=False)
    op.create_table('bilans_hydriques',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('espace_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('reserve_utile_fin_journee', sa.Float(), nullable=False),
    sa.Column('indice_stress', sa.Float(), nullable=False),
    sa.Column('statut_hydrique', sa.String(), nullable=False),
    sa.Column('stress_sanitaire', sa.Float(), nullable=True),
    sa.CheckConstraint("statut_hydrique IN ('Optimal', 'A surveiller', 'Critique')", name=op.f('ck_bilans_hydriques_statut')),
    sa.ForeignKeyConstraint(['espace_id'], ['espaces_verts.id'], name=op.f('fk_bilans_hydriques_espace_id_espaces_verts'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_bilans_hydriques')),
    sa.UniqueConstraint('espace_id', 'date', name='uq_bilans_hydriques_espace_date')
    )
    op.create_index(op.f('ix_bilans_hydriques_espace_id'), 'bilans_hydriques', ['espace_id'], unique=False)
    op.create_index(op.f('ix_bilans_hydriques_id'), 'bilans_hydriques', ['id'], unique=False)
    op.create_table('capteurs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nom', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('emplacement', sa.String(), nullable=True),
    sa.Column('espace_id', sa.Integer(), nullable=False),
    sa.Column('est_actif', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['espace_id'], ['espaces_verts.id'], name=op.f('fk_capteurs_espace_id_espaces_verts'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_capteurs'))
    )
    op.create_index(op.f('ix_capteurs_espace_id'), 'capteurs', ['espace_id'], unique=False)
    op.create_index(op.f('ix_capteurs_id'), 'capteurs', ['id'], unique=False)
    op.create_table('interventions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('espace_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=30), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('volume_eau_l', sa.Float(), nullable=True),
    sa.Column('statut', sa.String(length=20), server_default='planifiee', nullable=False),
    sa.Column('planifiee_le', sa.DateTime(timezone=True), nullable=True),
    sa.Column('realisee_le', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cree_le', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.Column('cree_par', sa.Integer(), nullable=True),
    sa.CheckConstraint("statut IN ('planifiee', 'en_cours', 'terminee')", name=op.f('ck_interventions_statut')),
    sa.CheckConstraint("type IN ('arrosage', 'ombrage', 'taille', 'fertilisation', 'traitement', 'nettoyage', 'diagnostic')", name=op.f('ck_interventions_type')),
    sa.ForeignKeyConstraint(['cree_par'], ['users.id'], name=op.f('fk_interventions_cree_par_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['espace_id'], ['espaces_verts.id'], name=op.f('fk_interventions_espace_id_espaces_verts'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_interventions'))
    )
    op.create_index(op.f('ix_interventions_espace_id'), 'interventions', ['espace_id'], unique=False)
    op.create_index(op.f('ix_interventions_id'), 'interventions', ['id'], unique=False)
    op.create_table('mesures',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('espace_id', sa.Integer(), nullable=False),
    sa.Column('temperature', sa.Float(), nullable=True),
    sa.Column('humidite_sol', sa.Float(), nullable=True),
    sa.Column('humidite_air', sa.Float(), nullable=True),
    sa.Column('co2', sa.Float(), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    sa.ForeignKeyConstraint(['espace_id'], ['espaces_verts.id'], name=op.f('fk_mesures_espace_id_espaces_verts'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_mesures'))
    )
    op.create_index('ix_mesures_espace_timestamp', 'mesures', ['espace_id', 'timestamp'], unique=False)
    op.create_index(op.f('ix_mesures_id'), 'mesures', ['id'], unique=False)
    op.create_table('zone_espaces',
    sa.Column('zone_id', sa.Integer(), nullable=False),
    sa.Column('espace_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['espace_id'], ['espaces_verts.id'], name=op.f('fk_zone_espaces_espace_id_espaces_verts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['zone_id'], ['zones_intelligentes.id'], name=op.f('fk_zone_espaces_zone_id_zones_intelligentes'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('zone_id', 'espace_id', name=op.f('pk_zone_espaces'))
    )


def downgrade() -> None:
    op.drop_table('zone_espaces')
    op.drop_index(op.f('ix_mesures_id'), table_name='mesures')
    op.drop_index('ix_mesures_espace_timestamp', table_name='mesures')
    op.drop_table('mesures')
    op.drop_index(op.f('ix_interventions_id'), table_name='interventions')
    op.drop_index(op.f('ix_interventions_espace_id'), table_name='interventions')
    op.drop_table('interventions')
    op.drop_index(op.f('ix_capteurs_id'), table_name='capteurs')
    op.drop_index(op.f('ix_capteurs_espace_id'), table_name='capteurs')
    op.drop_table('capteurs')
    op.drop_index(op.f('ix_bilans_hydriques_id'), table_name='bilans_hydriques')
    op.drop_index(op.f('ix_bilans_hydriques_espace_id'), table_name='bilans_hydriques')
    op.drop_table('bilans_hydriques')
    op.drop_index(op.f('ix_alertes_id'), table_name='alertes')
    op.drop_index(op.f('ix_alertes_espace_id'), table_name='alertes')
    op.drop_table('alertes')
    op.drop_index(op.f('ix_actions_irrigation_id'), table_name='actions_irrigation')
    op.drop_index(op.f('ix_actions_irrigation_espace_id'), table_name='actions_irrigation')
    op.drop_table('actions_irrigation')
    op.drop_index(op.f('ix_zones_intelligentes_user_id'), table_name='zones_intelligentes')
    op.drop_index(op.f('ix_zones_intelligentes_id'), table_name='zones_intelligentes')
    op.drop_table('zones_intelligentes')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_espaces_verts_user_id'), table_name='espaces_verts')
    op.drop_index(op.f('ix_espaces_verts_id'), table_name='espaces_verts')
    op.drop_table('espaces_verts')
    op.drop_index(op.f('ix_clustering_configs_user_id'), table_name='clustering_configs')
    op.drop_index(op.f('ix_clustering_configs_id'), table_name='clustering_configs')
    op.drop_table('clustering_configs')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_types_alertes_id'), table_name='types_alertes')
    op.drop_index(op.f('ix_types_alertes_code'), table_name='types_alertes')
    op.drop_table('types_alertes')
    op.drop_index(op.f('ix_plantes_nom_scientifique'), table_name='plantes')
    op.drop_index(op.f('ix_plantes_id'), table_name='plantes')
    op.drop_table('plantes')
    op.drop_index(op.f('ix_niveaux_alertes_id'), table_name='niveaux_alertes')
    op.drop_index(op.f('ix_niveaux_alertes_code'), table_name='niveaux_alertes')
    op.drop_table('niveaux_alertes')
    op.drop_index(op.f('ix_especes_vegetales_nom_scientifique'), table_name='especes_vegetales')
    op.drop_index(op.f('ix_especes_vegetales_id'), table_name='especes_vegetales')
    op.drop_table('especes_vegetales')
    op.drop_index(op.f('ix_auxiliaires_nom'), table_name='auxiliaires')
    op.drop_index(op.f('ix_auxiliaires_id'), table_name='auxiliaires')
    op.drop_table('auxiliaires')
