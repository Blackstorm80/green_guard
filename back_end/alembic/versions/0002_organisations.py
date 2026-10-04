"""Multi-organisations : organisations, rôles fins, patrimoine partagé, isolation par la base (RLS).

Données existantes : une « Organisation par défaut » (slug defaut) reçoit tous les utilisateurs et
tous les espaces ; rôles admin → admin, manager → gestionnaire, user → gestionnaire. L'ancien
propriétaire d'un espace devient son créateur (cree_par). Zones et configurations de clustering
passent à l'organisation de leur ancien utilisateur.

Row Level Security (PostgreSQL uniquement, FORCE : s'applique aussi au propriétaire des tables) :
- tables portant organisation_id : comparaison directe au paramètre app.organisation_id ;
- tables rattachées à un espace : sous-requête EXISTS sur espaces_verts, elle-même filtrée par sa
  politique. Choix préféré à une colonne organisation_id dénormalisée : aucune copie à maintenir
  cohérente (insertion, déplacement d'un espace), une seule source de vérité, et l'index de clé
  primaire d'espaces_verts rend la sous-requête peu coûteuse ;
- notifications : par utilisateur, via une sous-requête EXISTS sur users.
NULLIF(…, '') : après un premier SET LOCAL, current_setting renvoie '' (et non NULL) hors contexte ;
sans NULLIF, le transtypage ''::integer ferait échouer toute requête au lieu de ne rien renvoyer.

Revision ID: 0002_organisations
Revises: 0001_schema_v1
Create Date: 2026-10-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_organisations"
down_revision: Union[str, None] = "0001_schema_v1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NOUVEAUX_ROLES = "role IN ('admin', 'gestionnaire', 'technicien', 'lecteur')"
ANCIENS_ROLES = "role IN ('admin', 'manager', 'user')"

POLITIQUE = "isolation_organisation"
POLITIQUE_LECTURE = "lecture_configuration_instance"
ORGANISATION_COURANTE = "NULLIF(current_setting('app.organisation_id', true), '')::integer"
CONTOURNEMENT = "current_setting('app.contourner_rls', true) = 'on'"
TABLES_PAR_ESPACE = (
    "actions_irrigation", "alertes", "bilans_hydriques", "capteurs", "interventions", "mesures", "zone_espaces",
)


def _conditions_rls() -> dict[str, str]:
    conditions = {
        "organisations": f"id = {ORGANISATION_COURANTE}",
        "users": f"organisation_id = {ORGANISATION_COURANTE}",
        "espaces_verts": f"organisation_id = {ORGANISATION_COURANTE}",
        "zones_intelligentes": f"organisation_id = {ORGANISATION_COURANTE}",
        "clustering_configs": f"organisation_id = {ORGANISATION_COURANTE}",
        "notifications": "EXISTS (SELECT 1 FROM users u WHERE u.id = notifications.user_id)",
    }
    for table in TABLES_PAR_ESPACE:
        conditions[table] = f"EXISTS (SELECT 1 FROM espaces_verts e WHERE e.id = {table}.espace_id)"
    return {table: f"({condition}) OR {CONTOURNEMENT}" for table, condition in conditions.items()}


def _activer_rls() -> None:
    for table, condition in _conditions_rls().items():
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY {POLITIQUE} ON {table} USING ({condition}) WITH CHECK ({condition})")
    # Configuration par défaut de l'instance (organisation_id NULL) : lisible par tous, modifiable par aucun
    op.execute(
        f"CREATE POLICY {POLITIQUE_LECTURE} ON clustering_configs FOR SELECT USING (organisation_id IS NULL)"
    )


def _desactiver_rls() -> None:
    op.execute(f"DROP POLICY IF EXISTS {POLITIQUE_LECTURE} ON clustering_configs")
    for table in _conditions_rls():
        op.execute(f"DROP POLICY IF EXISTS {POLITIQUE} ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def _organisation_de(table: str, colonne: str = "user_id") -> str:
    return f"(SELECT u.organisation_id FROM users u WHERE u.id = {table}.{colonne})"


def _membre_de_reference(table: str) -> str:
    """Pour revenir au modèle mono-utilisateur : un administrateur de l'organisation, sinon un membre."""
    return (
        f"(SELECT u.id FROM users u WHERE u.organisation_id = {table}.organisation_id "
        "ORDER BY CASE WHEN u.role = 'admin' THEN 0 ELSE 1 END, u.id LIMIT 1)"
    )


def upgrade() -> None:
    bind = op.get_bind()
    op.create_table(
        "organisations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("parametres", sa.JSON(), nullable=True),
        sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organisations")),
    )
    op.create_index(op.f("ix_organisations_id"), "organisations", ["id"], unique=False)
    op.create_index(op.f("ix_organisations_slug"), "organisations", ["slug"], unique=True)

    # --- Utilisateurs : organisation, rôles fins, superadmin ---
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("organisation_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("est_superadmin", sa.Boolean(), server_default=sa.false(), nullable=False))
        batch.drop_constraint(op.f("ck_users_role"), type_="check")

    if bind.execute(sa.text("SELECT COUNT(*) FROM users")).scalar():
        bind.execute(sa.text("INSERT INTO organisations (nom, slug) VALUES (:nom, :slug)"),
                     {"nom": "Organisation par défaut", "slug": "defaut"})
        organisation_id = bind.execute(sa.text("SELECT id FROM organisations WHERE slug = 'defaut'")).scalar()
        bind.execute(sa.text("UPDATE users SET organisation_id = :o"), {"o": organisation_id})
    bind.execute(sa.text("UPDATE users SET role = 'gestionnaire' WHERE role IN ('manager', 'user')"))

    with op.batch_alter_table("users") as batch:
        batch.alter_column("organisation_id", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("role", existing_type=sa.String(), existing_nullable=False, server_default="lecteur")
        batch.create_check_constraint(op.f("ck_users_role"), NOUVEAUX_ROLES)
        batch.create_index(op.f("ix_users_organisation_id"), ["organisation_id"], unique=False)
        batch.create_foreign_key(op.f("fk_users_organisation_id_organisations"), "organisations",
                                 ["organisation_id"], ["id"], ondelete="CASCADE")

    # --- Espaces : propriété de l'organisation, l'ancien propriétaire devient le créateur ---
    with op.batch_alter_table("espaces_verts") as batch:
        batch.add_column(sa.Column("organisation_id", sa.Integer(), nullable=True))
    bind.execute(sa.text(f"UPDATE espaces_verts SET organisation_id = {_organisation_de('espaces_verts')}"))
    with op.batch_alter_table("espaces_verts") as batch:
        batch.drop_constraint(op.f("fk_espaces_verts_user_id_users"), type_="foreignkey")
        batch.drop_index(op.f("ix_espaces_verts_user_id"))
        batch.alter_column("user_id", new_column_name="cree_par", existing_type=sa.Integer(), nullable=True)
        batch.alter_column("organisation_id", existing_type=sa.Integer(), nullable=False)
        batch.create_index(op.f("ix_espaces_verts_organisation_id"), ["organisation_id"], unique=False)
        batch.create_foreign_key(op.f("fk_espaces_verts_organisation_id_organisations"), "organisations",
                                 ["organisation_id"], ["id"], ondelete="CASCADE")
    # Lot séparé : sous SQLite, une clé étrangère sur une colonne renommée dans le même lot est ignorée
    with op.batch_alter_table("espaces_verts") as batch:
        batch.create_foreign_key(op.f("fk_espaces_verts_cree_par_users"), "users",
                                 ["cree_par"], ["id"], ondelete="SET NULL")

    # --- Zones et configurations de clustering : par organisation ---
    for table, obligatoire in (("zones_intelligentes", True), ("clustering_configs", False)):
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("organisation_id", sa.Integer(), nullable=True))
        bind.execute(sa.text(f"UPDATE {table} SET organisation_id = {_organisation_de(table)} "
                             "WHERE user_id IS NOT NULL"))
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(op.f(f"fk_{table}_user_id_users"), type_="foreignkey")
            batch.drop_index(op.f(f"ix_{table}_user_id"))
            batch.drop_column("user_id")
            batch.alter_column("organisation_id", existing_type=sa.Integer(), nullable=not obligatoire)
            batch.create_index(op.f(f"ix_{table}_organisation_id"), ["organisation_id"], unique=False)
            batch.create_foreign_key(op.f(f"fk_{table}_organisation_id_organisations"), "organisations",
                                     ["organisation_id"], ["id"], ondelete="CASCADE")

    if bind.dialect.name == "postgresql":
        _activer_rls()


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        _desactiver_rls()

    # Retour au modèle mono-utilisateur : chaque objet revient à un membre de son organisation
    for table, obligatoire in (("clustering_configs", False), ("zones_intelligentes", True)):
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        bind.execute(sa.text(f"UPDATE {table} SET user_id = {_membre_de_reference(table)} "
                             "WHERE organisation_id IS NOT NULL"))
        bind.execute(sa.text(f"DELETE FROM {table} WHERE organisation_id IS NOT NULL AND user_id IS NULL"))
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(op.f(f"fk_{table}_organisation_id_organisations"), type_="foreignkey")
            batch.drop_index(op.f(f"ix_{table}_organisation_id"))
            batch.drop_column("organisation_id")
            batch.alter_column("user_id", existing_type=sa.Integer(), nullable=not obligatoire)
            batch.create_index(op.f(f"ix_{table}_user_id"), ["user_id"], unique=False)
            batch.create_foreign_key(op.f(f"fk_{table}_user_id_users"), "users", ["user_id"], ["id"],
                                     ondelete="CASCADE")

    bind.execute(sa.text(f"UPDATE espaces_verts SET cree_par = {_membre_de_reference('espaces_verts')} "
                         "WHERE cree_par IS NULL"))
    bind.execute(sa.text("DELETE FROM espaces_verts WHERE cree_par IS NULL"))
    with op.batch_alter_table("espaces_verts") as batch:
        batch.drop_constraint(op.f("fk_espaces_verts_cree_par_users"), type_="foreignkey")
        batch.drop_constraint(op.f("fk_espaces_verts_organisation_id_organisations"), type_="foreignkey")
        batch.drop_index(op.f("ix_espaces_verts_organisation_id"))
        batch.drop_column("organisation_id")
        batch.alter_column("cree_par", new_column_name="user_id", existing_type=sa.Integer(), nullable=False)
    with op.batch_alter_table("espaces_verts") as batch:
        batch.create_index(op.f("ix_espaces_verts_user_id"), ["user_id"], unique=False)
        batch.create_foreign_key(op.f("fk_espaces_verts_user_id_users"), "users", ["user_id"], ["id"],
                                 ondelete="CASCADE")

    with op.batch_alter_table("users") as batch:
        batch.drop_constraint(op.f("ck_users_role"), type_="check")
    bind.execute(sa.text("UPDATE users SET role = 'manager' WHERE role = 'gestionnaire'"))
    bind.execute(sa.text("UPDATE users SET role = 'user' WHERE role IN ('technicien', 'lecteur')"))
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint(op.f("fk_users_organisation_id_organisations"), type_="foreignkey")
        batch.drop_index(op.f("ix_users_organisation_id"))
        batch.drop_column("organisation_id")
        batch.drop_column("est_superadmin")
        batch.alter_column("role", existing_type=sa.String(), existing_nullable=False, server_default="user")
        batch.create_check_constraint(op.f("ck_users_role"), ANCIENS_ROLES)

    op.drop_index(op.f("ix_organisations_slug"), table_name="organisations")
    op.drop_index(op.f("ix_organisations_id"), table_name="organisations")
    op.drop_table("organisations")
