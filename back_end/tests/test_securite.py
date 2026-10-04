"""Sécurité : session par cookie httpOnly, CSRF, JWT, limitation de débit, en-têtes, erreurs génériques."""
from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from api.deps.auth import ALGORITHM, create_access_token
from api.v1.endpoints.meteo import get_meteo_service
from config import settings
from main import app
from tests.conftest import MOT_DE_PASSE, creer_compte

API = "/api/v1"
CSRF = {"X-Requested-With": "greenguard"}


def _inscrire_et_connecter_par_cookie(client: TestClient, email: str = "alice@example.com"):
    client.post(f"{API}/auth/register", json={"name": "Alice", "email": email, "password": MOT_DE_PASSE})
    return client.post(f"{API}/auth/login", data={"username": email, "password": MOT_DE_PASSE})


def test_login_pose_un_cookie_httponly(client):
    r = _inscrire_et_connecter_par_cookie(client)
    cookie = r.headers["set-cookie"]
    assert settings.cookie_name in cookie
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/api" in cookie
    assert "expires_at" in r.json()


def test_session_par_cookie_seul(client):
    _inscrire_et_connecter_par_cookie(client)
    assert client.get(f"{API}/users/me").status_code == 200  # aucun en-tête Authorization


def test_ecriture_par_cookie_exige_l_en_tete_csrf(client):
    _inscrire_et_connecter_par_cookie(client)
    espace = {"nom": "Parc", "latitude": 45.7, "longitude": 4.8}
    assert client.post(f"{API}/espaces-verts/", json=espace).status_code == 403
    assert client.post(f"{API}/espaces-verts/", json=espace, headers=CSRF).status_code == 201


def test_bearer_n_exige_pas_l_en_tete_csrf(client):
    headers = creer_compte(client)
    client.cookies.clear()
    r = client.post(f"{API}/espaces-verts/", json={"nom": "Parc", "latitude": 45.7, "longitude": 4.8}, headers=headers)
    assert r.status_code == 201


def test_logout_supprime_la_session(client):
    _inscrire_et_connecter_par_cookie(client)
    assert client.post(f"{API}/auth/logout").status_code == 204
    assert client.get(f"{API}/users/me").status_code == 401


def test_jeton_falsifie_refuse(client):
    creer_compte(client)
    client.cookies.clear()
    faux = jwt.encode({"sub": "alice@example.com", "exp": datetime.now(UTC) + timedelta(hours=1),
                       "type": "access"}, "mauvaise-cle-mais-assez-longue-0123456789", algorithm=ALGORITHM)
    assert client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {faux}"}).status_code == 401


def test_jeton_expire_refuse(client):
    creer_compte(client)
    client.cookies.clear()
    token, _ = create_access_token("alice@example.com", expires_delta=timedelta(seconds=-1))
    assert client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_jeton_d_un_autre_type_refuse(client):
    creer_compte(client)
    client.cookies.clear()
    token = jwt.encode({"sub": "alice@example.com", "exp": datetime.now(UTC) + timedelta(hours=1),
                        "type": "refresh"}, settings.secret_key, algorithm=ALGORITHM)
    assert client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_limitation_de_debit_sur_le_login(client):
    for _ in range(settings.auth_rate_limit):
        client.post(f"{API}/auth/login", data={"username": "x@example.com", "password": "mauvais-mot-de-passe"})
    r = client.post(f"{API}/auth/login", data={"username": "x@example.com", "password": "mauvais-mot-de-passe"})
    assert r.status_code == 429
    assert "Retry-After" in r.headers


def test_en_tetes_de_securite(client):
    r = client.get(f"{API}/health/live")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Request-ID"]
    # Swagger doit rester utilisable (scripts CDN) : pas de CSP stricte sur /docs
    assert "Content-Security-Policy" not in client.get("/docs").headers


def test_erreur_interne_generique_sans_trace(client):
    headers = creer_compte(client)

    class MeteoEnPanne:
        def recuperer_conditions_actuelles(self, *args, **kwargs):
            raise RuntimeError("détail technique secret")

    app.dependency_overrides[get_meteo_service] = lambda: MeteoEnPanne()
    r = TestClient(app, raise_server_exceptions=False).get(f"{API}/meteo/Lyon", headers=headers)
    assert r.status_code == 500
    assert "secret" not in r.text
    assert r.json()["detail"] == "Erreur interne du serveur." and r.json()["request_id"]


def test_cors_refuse_une_origine_inconnue(client):
    r = client.options(f"{API}/users/me", headers={"Origin": "https://pirate.example",
                                                   "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_secret_trop_court_refuse(monkeypatch):
    import pytest

    from config import Settings
    monkeypatch.setenv("SECRET_KEY", "trop-courte")
    with pytest.raises(RuntimeError, match="trop courte"):
        Settings()


def test_dependances_bdd_synchrones():
    """Non-régression (recette phase 4) : une dépendance `async` qui interroge la base bloque la boucle
    d'événements en attendant une connexion du pool ; sous charge, l'API entière se fige."""
    import inspect

    from api.deps.auth import exiger_role, exiger_superadmin, get_current_user
    assert not inspect.iscoroutinefunction(get_current_user)
    assert not inspect.iscoroutinefunction(exiger_role("admin"))
    assert not inspect.iscoroutinefunction(exiger_superadmin)
