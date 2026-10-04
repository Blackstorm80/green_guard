"""La migration Alembic doit produire exactement le schéma des modèles (aucune dérive)
et migrer les données existantes sans perte."""
import os
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from infrastructure.database import Base

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def config_alembic(monkeypatch, url: str) -> Config:
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(os.path.join(BACKEND, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(BACKEND, "alembic"))
    return config


def test_migrations_sans_derive(monkeypatch):
    url = f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'migration.db')}"
    config = config_alembic(monkeypatch, url)

    command.upgrade(config, "head")
    engine = create_engine(url)
    with engine.connect() as conn:
        assert compare_metadata(MigrationContext.configure(conn), Base.metadata) == []

    command.downgrade(config, "base")
    command.upgrade(config, "head")
    engine.dispose()


def _inserer_donnees_v1(conn) -> None:
    """Base mono-utilisateur (schéma 0001) : trois comptes, leurs espaces, zones et configurations."""
    conn.execute(text(
        "INSERT INTO users (id, name, email, hashed_password, role) VALUES "
        "(1, 'Admin', 'admin@example.com', 'h', 'admin'), (2, 'Manon', 'manon@example.com', 'h', 'manager'), "
        "(3, 'Ugo', 'ugo@example.com', 'h', 'user')"
    ))
    conn.execute(text(
        "INSERT INTO espaces_verts (id, nom, latitude, longitude, user_id) VALUES "
        "(10, 'Parc Admin', 45.7, 4.8, 1), (11, 'Square Ugo', 45.8, 4.9, 3)"
    ))
    conn.execute(text("INSERT INTO mesures (espace_id, temperature) VALUES (11, 21.5)"))
    conn.execute(text("INSERT INTO zones_intelligentes (id, nom, user_id) VALUES (20, 'Zone Ugo', 3)"))
    conn.execute(text(
        "INSERT INTO clustering_configs (id, nom_config, user_id, n_clusters) VALUES "
        "(30, 'instance', NULL, 5), (31, 'perso', 2, 3)"
    ))
    conn.execute(text("INSERT INTO notifications (user_id, message) VALUES (3, 'Bonjour')"))


def verifier_migration_des_donnees(monkeypatch, url: str) -> None:
    config = config_alembic(monkeypatch, url)
    command.upgrade(config, "0001_schema_v1")
    engine = create_engine(url)
    with engine.begin() as conn:
        _inserer_donnees_v1(conn)

    command.upgrade(config, "head")
    with engine.begin() as conn:
        # Lecture hors contexte d'organisation (PostgreSQL : RLS désormais active)
        if conn.dialect.name == "postgresql":
            conn.execute(text("SELECT set_config('app.contourner_rls', 'on', true)"))
        organisation = conn.execute(text("SELECT id, nom, slug FROM organisations")).one()
        assert (organisation.nom, organisation.slug) == ("Organisation par défaut", "defaut")
        roles = dict(conn.execute(text("SELECT email, role FROM users WHERE organisation_id = :o"),
                                  {"o": organisation.id}).all())
        assert roles == {"admin@example.com": "admin", "manon@example.com": "gestionnaire",
                         "ugo@example.com": "gestionnaire"}
        assert conn.execute(text("SELECT COUNT(*) FROM users WHERE est_superadmin")).scalar() == 0
        espaces = conn.execute(text("SELECT id, organisation_id, cree_par FROM espaces_verts ORDER BY id")).all()
        assert [tuple(e) for e in espaces] == [(10, organisation.id, 1), (11, organisation.id, 3)]
        assert conn.execute(text("SELECT COUNT(*) FROM mesures")).scalar() == 1
        assert conn.execute(text("SELECT organisation_id FROM zones_intelligentes")).scalar() == organisation.id
        configs = dict(conn.execute(text("SELECT nom_config, organisation_id FROM clustering_configs")).all())
        assert configs == {"instance": None, "perso": organisation.id}
        assert conn.execute(text("SELECT COUNT(*) FROM notifications")).scalar() == 1
    # Les anciens rôles sont désormais refusés par la contrainte CHECK
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("UPDATE users SET role = 'manager' WHERE id = 1"))

    command.downgrade(config, "0001_schema_v1")
    with engine.begin() as conn:
        assert dict(conn.execute(text("SELECT email, role FROM users")).all()) == {
            "admin@example.com": "admin", "manon@example.com": "manager", "ugo@example.com": "manager"}
        assert [tuple(e) for e in conn.execute(text("SELECT id, user_id FROM espaces_verts ORDER BY id"))] == [
            (10, 1), (11, 3)]
        # La zone revient à un administrateur de l'organisation (l'utilisateur d'origine n'est plus connu)
        assert conn.execute(text("SELECT user_id FROM zones_intelligentes")).scalar() == 1
        assert conn.execute(text("SELECT COUNT(*) FROM mesures")).scalar() == 1
    engine.dispose()


def test_migration_organisations_rattache_les_donnees_existantes(monkeypatch):
    url = f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'donnees.db')}"
    verifier_migration_des_donnees(monkeypatch, url)


def test_migration_base_vide_sans_organisation_fantome(monkeypatch):
    url = f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'vide.db')}"
    command.upgrade(config_alembic(monkeypatch, url), "head")
    engine = create_engine(url)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM organisations")).scalar() == 0
    engine.dispose()


def test_migration_fao56_conserve_les_bilans_et_libere_la_reserve_par_defaut(monkeypatch):
    url = f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'fao56.db')}"
    config = config_alembic(monkeypatch, url)
    command.upgrade(config, "0002_organisations")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO organisations (id, nom, slug) VALUES (1, 'Ville', 'ville')"))
        conn.execute(text(
            "INSERT INTO espaces_verts (id, nom, latitude, longitude, organisation_id, reserve_utile_max, "
            "coefficient_cultural) VALUES (10, 'Défaut', 45.7, 4.8, 1, 100, 1), (11, 'Saisie', 45.8, 4.9, 1, 60, 0.7)"
        ))
        conn.execute(text(
            "INSERT INTO bilans_hydriques (espace_id, date, reserve_utile_fin_journee, indice_stress, "
            "statut_hydrique) VALUES (10, '2026-07-01', 70, 0.3, 'A surveiller')"
        ))

    command.upgrade(config, "head")
    with engine.begin() as conn:
        bilan = conn.execute(text("SELECT reserve_utile_fin_journee, indice_stress, version_modele, taw_mm, "
                                  "epuisement_fin_mm, source_meteo FROM bilans_hydriques")).one()
        assert tuple(bilan) == (70, 0.3, "historique-v1", None, None, None)
        espaces = conn.execute(text("SELECT id, reserve_utile_max, coefficient_cultural FROM espaces_verts "
                                    "ORDER BY id")).all()
        assert [tuple(e) for e in espaces] == [(10, None, 1), (11, 60, 0.7)]   # 100 = ancien défaut → calculée
        conn.execute(text("INSERT INTO espaces_verts (id, nom, latitude, longitude, organisation_id) "
                          "VALUES (12, 'Nouveau', 45.0, 4.0, 1)"))
        assert conn.execute(text("SELECT coefficient_cultural FROM espaces_verts WHERE id = 12")).scalar() == 0.8
        # Un nouveau bilan doit déclarer la version de son modèle
        with pytest.raises(IntegrityError):
            conn.execute(text("INSERT INTO bilans_hydriques (espace_id, date, reserve_utile_fin_journee, "
                              "indice_stress, statut_hydrique, version_modele) "
                              "VALUES (11, '2026-07-01', 1, 0, 'Optimal', NULL)"))

    command.downgrade(config, "0002_organisations")
    with engine.begin() as conn:
        assert dict(conn.execute(text("SELECT id, reserve_utile_max FROM espaces_verts")).all()) == {
            10: 100, 11: 60, 12: 100}
        assert conn.execute(text("SELECT reserve_utile_fin_journee FROM bilans_hydriques")).scalar() == 70
    engine.dispose()


def test_migration_boucle_arrosage_compte_les_arrosages_deja_termines(monkeypatch):
    url = f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'arrosage.db')}"
    config = config_alembic(monkeypatch, url)
    command.upgrade(config, "0003_moteur_fao56")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO organisations (id, nom, slug) VALUES (1, 'Ville', 'ville')"))
        conn.execute(text(
            "INSERT INTO espaces_verts (id, nom, latitude, longitude, organisation_id, surface_m2) VALUES "
            "(10, 'Mesuré', 45.7, 4.8, 1, 200), (11, 'Sans surface', 45.8, 4.9, 1, NULL)"
        ))
        conn.execute(text(
            "INSERT INTO interventions (id, espace_id, type, statut, volume_eau_l, realisee_le) VALUES "
            "(1, 10, 'arrosage', 'terminee', 1000, '2026-07-01 08:00:00'), "
            "(2, 10, 'arrosage', 'planifiee', 1000, NULL), (3, 10, 'taille', 'terminee', 1000, NULL), "
            "(4, 11, 'arrosage', 'terminee', 1000, NULL), (5, 10, 'arrosage', 'terminee', NULL, NULL), "
            "(6, 10, 'arrosage', 'terminee', 400, NULL)"
        ))
        # Apport saisi hors intervention : conservé tel quel
        conn.execute(text("INSERT INTO actions_irrigation (espace_id, quantite_mm) VALUES (10, 7)"))

    command.upgrade(config, "head")
    with engine.begin() as conn:
        apports = conn.execute(text(
            "SELECT intervention_id, quantite_mm, timestamp FROM actions_irrigation ORDER BY id")).all()
        assert [(a.intervention_id, a.quantite_mm) for a in apports] == [(None, 7), (1, 5), (6, 2)]
        assert str(apports[1].timestamp).startswith("2026-07-01 08:00")          # horodaté à la réalisation
        assert conn.execute(text("SELECT debit_arrosage_l_min FROM espaces_verts WHERE id = 10")).scalar() is None
        # Une intervention ne peut produire qu'un apport
        with pytest.raises(IntegrityError), conn.begin_nested():
            conn.execute(text("INSERT INTO actions_irrigation (espace_id, quantite_mm, intervention_id) "
                              "VALUES (10, 1, 1)"))

    command.downgrade(config, "0003_moteur_fao56")
    with engine.begin() as conn:
        assert conn.execute(text("SELECT quantite_mm FROM actions_irrigation")).scalars().all() == [7]
        assert conn.execute(text("SELECT COUNT(*) FROM interventions")).scalar() == 6
    engine.dispose()
