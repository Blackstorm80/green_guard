"""Isolation par la base (PostgreSQL uniquement) : la Row Level Security de la migration 0002 bloque
ce qu'un oubli de filtre applicatif laisserait passer.

Chaque scénario tourne sur une base dédiée, créée par les migrations Alembic (et non par create_all),
avec un rôle applicatif sans privilège : un superutilisateur ignorerait toujours la RLS.
"""
import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import DBAPIError

from alembic import command
from domain.models import EspaceVert
from infrastructure.database import SessionLocal, engine, get_db
from infrastructure.jobs.mise_a_jour_capteurs import executer_mise_a_jour
from infrastructure.rls import contournement_rls, definir_organisation, rls_effective
from main import app
from tests.conftest import MOT_DE_PASSE, connecter, creer_espace
from tests.test_migrations import config_alembic, verifier_migration_des_donnees

URL_TEST = os.getenv("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not URL_TEST.startswith("postgresql"), reason="RLS : PostgreSQL uniquement")

API = "/api/v1"
ROLE_APPLICATIF = "gg_rls_app"
CREER_ROLE_APPLICATIF = (
    "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gg_rls_app') THEN "
    "CREATE ROLE gg_rls_app NOLOGIN NOSUPERUSER NOBYPASSRLS; END IF; END $$"
)


def _serveur() -> Engine:
    return create_engine(URL_TEST, isolation_level="AUTOCOMMIT")


def _recreer_base(nom: str) -> str:
    serveur = _serveur()
    with serveur.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{nom}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{nom}"'))
    serveur.dispose()
    return make_url(URL_TEST).set(database=nom).render_as_string(hide_password=False)


def _supprimer_base(nom: str) -> None:
    serveur = _serveur()
    with serveur.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{nom}" WITH (FORCE)'))
    serveur.dispose()


@pytest.fixture(scope="module")
def base_rls() -> Iterator[dict]:
    """Base migrée, rôle applicatif, deux organisations avec chacune un espace, une mesure, une notification."""
    url = _recreer_base("gg_rls_test")
    with pytest.MonkeyPatch.context() as mp:
        command.upgrade(config_alembic(mp, url), "head")

    superutilisateur = create_engine(url)
    with superutilisateur.begin() as conn:
        conn.execute(text(CREER_ROLE_APPLICATIF))
        conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {ROLE_APPLICATIF}"))
        conn.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {ROLE_APPLICATIF}"))
        conn.execute(text(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {ROLE_APPLICATIF}"))
        ids = {}
        for lettre in ("a", "b"):
            org = conn.execute(text("INSERT INTO organisations (nom, slug) VALUES (:n, :s) RETURNING id"),
                               {"n": f"Ville {lettre.upper()}", "s": f"ville-{lettre}"}).scalar()
            user = conn.execute(text(
                "INSERT INTO users (name, email, hashed_password, organisation_id, role) "
                "VALUES (:n, :e, 'h', :o, 'admin') RETURNING id"), {"n": lettre, "e": f"{lettre}@rls.test", "o": org},
            ).scalar()
            espace = conn.execute(text(
                "INSERT INTO espaces_verts (nom, latitude, longitude, organisation_id, cree_par) "
                "VALUES (:n, 45.7, 4.8, :o, :u) RETURNING id"), {"n": f"Parc {lettre.upper()}", "o": org, "u": user},
            ).scalar()
            conn.execute(text("INSERT INTO mesures (espace_id, temperature) VALUES (:e, 20)"), {"e": espace})
            conn.execute(text("INSERT INTO notifications (user_id, message) VALUES (:u, 'n')"), {"u": user})
            ids[lettre] = {"organisation": org, "user": user, "espace": espace}

    moteur_app = create_engine(url)

    @event.listens_for(moteur_app, "connect")
    def _role_applicatif(connexion_dbapi, _):
        with connexion_dbapi.cursor() as curseur:
            curseur.execute(f"SET ROLE {ROLE_APPLICATIF}")
        connexion_dbapi.commit()   # sinon annulé avec la transaction implicite de psycopg2

    yield {"url": url, "app": moteur_app, "superutilisateur": superutilisateur, **ids}

    moteur_app.dispose()
    superutilisateur.dispose()
    _supprimer_base("gg_rls_test")
    serveur = _serveur()
    with serveur.connect() as conn:
        conn.execute(text(f"DROP ROLE IF EXISTS {ROLE_APPLICATIF}"))
    serveur.dispose()


def _contexte(conn, organisation_id=None, contourner=False) -> None:
    conn.execute(text("SELECT set_config('app.organisation_id', :o, true), set_config('app.contourner_rls', :c, true)"),
                 {"o": "" if organisation_id is None else str(organisation_id), "c": "on" if contourner else "off"})


def _compter(conn, table: str) -> int:
    return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()  # noqa: S608 (nom de table interne)


def test_le_role_applicatif_est_soumis_a_la_rls(base_rls):
    assert rls_effective(base_rls["app"]) is True
    assert rls_effective(engine) is False          # superutilisateur des tests : RLS ignorée, d'où l'avertissement


def test_rls_bloque_une_requete_sql_brute_sans_contexte(base_rls):
    with base_rls["app"].connect() as conn:
        for table in ("organisations", "users", "espaces_verts", "mesures", "notifications"):
            assert _compter(conn, table) == 0, table           # aucune ligne, et aucune erreur


def test_rls_limite_a_l_organisation_du_contexte(base_rls):
    a, b = base_rls["a"], base_rls["b"]
    with base_rls["app"].connect() as conn:
        with conn.begin():
            _contexte(conn, a["organisation"])
            assert conn.execute(text("SELECT nom FROM espaces_verts")).scalars().all() == ["Parc A"]
            assert conn.execute(text("SELECT espace_id FROM mesures")).scalars().all() == [a["espace"]]
            assert conn.execute(text("SELECT user_id FROM notifications")).scalars().all() == [a["user"]]
            assert conn.execute(text("SELECT slug FROM organisations")).scalars().all() == ["ville-a"]
            # Modifier ou supprimer chez l'autre : aucune ligne atteinte
            assert conn.execute(text("UPDATE espaces_verts SET nom = 'pirate' WHERE id = :e"),
                                {"e": b["espace"]}).rowcount == 0
            assert conn.execute(text("DELETE FROM mesures WHERE espace_id = :e"), {"e": b["espace"]}).rowcount == 0

        # Écrire chez l'autre : refusé par WITH CHECK
        for requete, params in [
            ("INSERT INTO espaces_verts (nom, latitude, longitude, organisation_id) VALUES ('x', 1, 1, :o)",
             {"o": b["organisation"]}),
            ("INSERT INTO mesures (espace_id, temperature) VALUES (:e, 1)", {"e": b["espace"]}),
        ]:
            with pytest.raises(DBAPIError, match="row-level security"), conn.begin():
                _contexte(conn, a["organisation"])
                conn.execute(text(requete), params)

        # Piège : le contexte (local à la transaction) a disparu au commit, sans faire échouer la requête
        with conn.begin():
            assert _compter(conn, "espaces_verts") == 0
        with conn.begin():
            _contexte(conn, contourner=True)
            assert _compter(conn, "espaces_verts") == 2


def test_rls_restrictions_secheresse(base_rls):
    """Table du mode sécheresse (migration 0006) : cloisonnée par l'espace, comme les autres."""
    a, b = base_rls["a"], base_rls["b"]
    with base_rls["superutilisateur"].begin() as conn:
        for espace in (a["espace"], b["espace"]):
            conn.execute(text("INSERT INTO restrictions_secheresse (espace_id, date, niveau) "
                              "VALUES (:e, '2026-07-01', 'crise') ON CONFLICT DO NOTHING"), {"e": espace})
    with base_rls["app"].connect() as conn:
        with conn.begin():
            assert _compter(conn, "restrictions_secheresse") == 0      # sans contexte : rien
        with conn.begin():
            _contexte(conn, a["organisation"])
            assert conn.execute(text("SELECT espace_id FROM restrictions_secheresse")).scalars().all() == [a["espace"]]
            assert conn.execute(text("UPDATE restrictions_secheresse SET niveau = 'aucune' WHERE espace_id = :e"),
                                {"e": b["espace"]}).rowcount == 0
        with pytest.raises(DBAPIError, match="row-level security"), conn.begin():
            _contexte(conn, a["organisation"])
            conn.execute(text("INSERT INTO restrictions_secheresse (espace_id, date, niveau) "
                              "VALUES (:e, '2026-07-02', 'aucune')"), {"e": b["espace"]})


def test_session_repose_le_contexte_a_chaque_transaction(base_rls):
    a = base_rls["a"]
    session = SessionLocal(bind=base_rls["app"])
    try:
        definir_organisation(session, a["organisation"])
        assert [e.nom for e in session.query(EspaceVert)] == ["Parc A"]
        session.commit()
        assert [e.nom for e in session.query(EspaceVert)] == ["Parc A"]     # après commit : toujours en contexte
        session.rollback()
        with contournement_rls(session):
            assert session.query(EspaceVert).count() == 2
            session.commit()
            assert session.query(EspaceVert).count() == 2                 # contournement reposé lui aussi
        assert session.query(EspaceVert).count() == 1                     # et levé à la sortie du bloc
    finally:
        session.close()


def test_parcours_api_sous_rls(base_rls, client, meteo):
    """L'application complète tourne sur la base protégée, connectée avec le rôle applicatif."""
    def get_db_rls():
        db = SessionLocal(bind=base_rls["app"])
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_db_rls
    entetes = {}
    for nom in ("alice", "bob"):
        r = client.post(f"{API}/auth/register", json={
            "name": nom, "email": f"{nom}@rls.example.com", "password": MOT_DE_PASSE, "organisation": f"Ville {nom}"})
        assert r.status_code == 201, r.text
        entetes[nom] = connecter(client, f"{nom}@rls.example.com")
    alice, bob = entetes["alice"], entetes["bob"]

    espace_alice = creer_espace(client, alice, nom="Parc d'Alice", reserve_utile_max=10, coefficient_cultural=1.0)
    creer_espace(client, bob, nom="Parc de Bob")
    assert [e["nom"] for e in client.get(f"{API}/espaces-verts/", headers=alice).json()] == ["Parc d'Alice"]
    assert client.get(f"{API}/espaces-verts/{espace_alice['id']}", headers=bob).status_code == 404
    assert client.post(f"{API}/interventions/", json={"espace_id": espace_alice["id"], "type": "arrosage"},
                       headers=alice).status_code == 201
    assert client.get(f"{API}/interventions/", headers=bob).json() == []
    assert client.get(f"{API}/users/me", headers=alice).json()["organisation"]["nom"] == "Ville alice"
    assert [m["email"] for m in client.get(f"{API}/organisations/moi/membres", headers=bob).json()] == [
        "bob@rls.example.com"]

    # Worker : toutes les organisations traitées, chacune dans son contexte
    meteo.et0 = 9.0
    session = SessionLocal(bind=base_rls["app"])
    try:
        executer_mise_a_jour(session, meteo_service=meteo)
    finally:
        session.close()
    assert client.get(f"{API}/capteurs/dashboard", headers=alice).json()["statut"] == "Critique"
    assert client.get(f"{API}/capteurs/dashboard", headers=bob).json()["statut"] == "Sain"
    assert len(client.get(f"{API}/notifications/", headers=alice).json()) == 1
    assert client.get(f"{API}/notifications/", headers=bob).json() == []
    assert client.post(f"{API}/zones/clustering/rebuild", headers=alice).status_code == 201
    assert client.get(f"{API}/zones/", headers=bob).json() == []
    assert client.get(f"{API}/vegetal/etat-global", headers=bob).json()["total_espaces"] == 1

    # Superadmin : la création d'une autre organisation passe par le contournement explicite
    with base_rls["superutilisateur"].begin() as conn:
        conn.execute(text("UPDATE users SET est_superadmin = true WHERE email = 'alice@rls.example.com'"))
    r = client.post(f"{API}/organisations/", headers=alice, json={
        "nom": "Métropole RLS", "admin": {"name": "M", "email": "m@rls.example.com", "password": MOT_DE_PASSE}})
    assert r.status_code == 201, r.text
    assert client.get(f"{API}/espaces-verts/", headers=connecter(client, "m@rls.example.com")).json() == []

    with base_rls["superutilisateur"].connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM bilans_hydriques b JOIN espaces_verts e ON e.id = b.espace_id "
                                 "WHERE e.nom IN ('Parc d''Alice', 'Parc de Bob')")).scalar() == 2


def test_migration_des_donnees_postgresql(monkeypatch):
    url = _recreer_base("gg_migration_test")
    try:
        verifier_migration_des_donnees(monkeypatch, url)
    finally:
        _supprimer_base("gg_migration_test")
