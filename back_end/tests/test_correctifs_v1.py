"""Correctifs avant la v1.0 (pistes_evolution.md § 0) : exposition réseau, limitation de débit
derrière un proxy, documentation interactive, jour du bilan en heure locale."""
import os
import subprocess
import sys
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from api.deps.rate_limit import LimiteurConnexion, RateLimiter
from api.v1.endpoints.auth import limiteur_connexion, limiteur_inscription
from application.use_cases.generer_bilans_hydriques_journaliers import generer_bilans_hydriques_journaliers
from config import settings
from domain.models import ActionIrrigation, BilanHydriqueJournalier, EspaceVert, Notification
from infrastructure.jobs.mise_a_jour_capteurs import executer_mise_a_jour
from main import app
from tests.conftest import MOT_DE_PASSE, creer_compte, creer_espace

API = "/api/v1"
BACK_END = Path(__file__).resolve().parents[1]
RACINE = BACK_END.parent
PARIS = ZoneInfo("Europe/Paris")


def _connexion(client, email, mot_de_passe="mauvais-mot-de-passe", ip=None):
    # TestClient accepte une IP cliente fictive : simule des postes distincts
    c = TestClient(app, client=(ip, 50000)) if ip else client
    return c.post(f"{API}/auth/login", data={"username": email, "password": mot_de_passe})


# --- Limitation de débit de la connexion ---------------------------------------

def test_quota_par_identifiant_ne_bloque_pas_les_autres_comptes(client):
    creer_compte(client, "alice@example.com")
    limiteur_connexion.reinitialiser()
    for _ in range(settings.auth_rate_limit):
        assert _connexion(client, "mallory-cible@example.com").status_code == 401
    assert _connexion(client, "mallory-cible@example.com").status_code == 429
    # Même IP (collectivité derrière un proxy) : les autres agents se connectent toujours
    assert _connexion(client, "alice@example.com", MOT_DE_PASSE).status_code == 200


def test_quota_par_identifiant_quelle_que_soit_l_ip(client):
    for i in range(settings.auth_rate_limit):
        assert _connexion(client, "bob@example.com", ip=f"203.0.113.{i + 1}").status_code == 401
    r = _connexion(client, "bob@example.com", ip="198.51.100.7")
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0


def test_identifiant_normalise_en_minuscules(client):
    for i in range(settings.auth_rate_limit):
        email = "Bob@Example.com" if i % 2 else "  bob@example.COM "
        assert _connexion(client, email).status_code == 401
    assert _connexion(client, "bob@example.com").status_code == 429


def test_le_429_ne_revele_pas_l_existence_du_compte(client):
    creer_compte(client, "alice@example.com")
    limiteur_connexion.reinitialiser()
    reponses = {}
    for email in ("alice@example.com", "inconnu@example.com"):
        for _ in range(settings.auth_rate_limit):
            assert _connexion(client, email).status_code == 401
        reponses[email] = _connexion(client, email)
    existant, inconnu = reponses["alice@example.com"], reponses["inconnu@example.com"]
    assert existant.status_code == inconnu.status_code == 429
    assert existant.json() == inconnu.json()


def test_quota_large_par_ip(client):
    app.dependency_overrides[limiteur_connexion] = LimiteurConnexion(max_par_ip=3, max_par_identifiant=10,
                                                                     fenetre_s=60)
    for i in range(3):
        assert _connexion(client, f"agent{i}@example.com").status_code == 401
    assert _connexion(client, "agent-suivant@example.com").status_code == 429
    # Une autre IP n'est pas concernée
    assert _connexion(client, "agent-suivant@example.com", ip="203.0.113.50").status_code == 401


def test_derriere_un_proxy_de_confiance_chaque_client_a_son_quota(meteo):
    """Chaîne de production : uvicorn (--proxy-headers, --forwarded-allow-ips=TRUSTED_PROXIES) puis l'API."""
    app.dependency_overrides[limiteur_connexion] = LimiteurConnexion(max_par_ip=2, max_par_identifiant=10,
                                                                     fenetre_s=60)

    def connexions(proxy_ip, confiance):
        c = TestClient(ProxyHeadersMiddleware(app, trusted_hosts=confiance), client=(proxy_ip, 40000))
        return [c.post(f"{API}/auth/login", headers={"X-Forwarded-For": f"198.51.100.{i}"},
                       data={"username": f"agent{i}@example.com", "password": "x"}).status_code
                for i in range(4)]

    assert connexions("127.0.0.1", settings.trusted_proxies) == [401, 401, 401, 401]
    # Proxy non déclaré : toutes les requêtes semblent venir de lui (le défaut corrigé)
    assert connexions("172.18.0.1", settings.trusted_proxies) == [401, 401, 429, 429]
    assert connexions("172.18.0.2", "172.16.0.0/12") == [401, 401, 401, 401]


def test_quota_ip_par_defaut_plus_large_que_le_quota_par_identifiant():
    assert settings.auth_rate_limit_ip == 100 and settings.auth_rate_limit == 10


def test_tentative_refusee_non_decomptee():
    limiteur = RateLimiter(max_requetes=2, fenetre_s=60)
    limiteur.consommer("cle")
    limiteur.consommer("cle")
    for _ in range(5):
        with pytest.raises(HTTPException, match="429"):
            limiteur.consommer("cle")
    assert len(limiteur._appels["cle"]) == 2


def test_cles_expirees_purgees(monkeypatch):
    from api.deps import rate_limit
    monkeypatch.setattr(rate_limit, "MAX_CLES_AVANT_PURGE", 3)
    instants = iter([0.0, 1.0, 2.0, 100.0, 100.0])
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: next(instants))
    limiteur = RateLimiter(max_requetes=5, fenetre_s=10)
    for cle in ("a", "b", "c"):
        limiteur.enregistrer(cle)
    limiteur.enregistrer("d")                     # t = 100 : a, b, c ont expiré
    assert set(limiteur._appels) == {"d"}


def test_inscription_toujours_limitee_par_ip(client):
    app.dependency_overrides[limiteur_inscription] = RateLimiter(max_requetes=2, fenetre_s=60)
    for i in range(2):
        r = client.post(f"{API}/auth/register",
                        json={"name": "A", "email": f"a{i}@example.com", "password": MOT_DE_PASSE})
        assert r.status_code == 201
    r = client.post(f"{API}/auth/register", json={"name": "A", "email": "a9@example.com", "password": MOT_DE_PASSE})
    assert r.status_code == 429


# --- Documentation interactive -------------------------------------------------

def test_documentation_fermee_par_defaut():
    """Import isolé dans un sous-processus : `settings` est lu une seule fois à l'import."""
    script = (
        "from fastapi.testclient import TestClient\n"
        "from main import app\n"
        "c = TestClient(app)\n"
        "print([c.get(p).status_code for p in ('/docs', '/redoc', '/openapi.json', '/api/v1/health/live')])\n"
    )
    env = {k: v for k, v in os.environ.items() if k not in ("ENABLE_DOCS", "TEST_DATABASE_URL")}
    env["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(prefix="gg-docs-"), "docs.db")
    env["SECRET_KEY"] = "cle-de-test-uniquement-0123456789abcdef"
    # .env local ignoré : load_dotenv ne remplace pas une variable déjà définie
    env["ENABLE_DOCS"] = ""
    resultat = subprocess.run([sys.executable, "-c", script], cwd=BACK_END, env=env,  # noqa: S603
                              capture_output=True, text=True, timeout=60, check=True)
    assert resultat.stdout.strip().splitlines()[-1] == "[404, 404, 404, 200]"


def test_documentation_ouverte_si_activee(client):
    assert settings.enable_docs is True                       # activée par conftest
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


# --- Jour du bilan en heure locale ---------------------------------------------

def test_bilan_date_du_jour_local_et_non_utc(meteo):
    espace = EspaceVert(id=1, nom="Parc", latitude=45.76, longitude=4.83, reserve_utile_max=100.0,
                        coefficient_cultural=1.0)

    class Depot:
        def __init__(self):
            self.enregistres = []

        def get_dernier_avant(self, espace_id, jour):
            return None

        def get_by_espace_and_date(self, espace_id, jour):
            return None

        def save(self, bilan):
            self.enregistres.append(bilan)
            return bilan

    depot = Depot()
    arrosages = []
    rapport = generer_bilans_hydriques_journaliers(
        espaces=[espace], bilan_repo=depot, meteo_service=meteo,
        arrosage_du_jour_mm=lambda espace_id, jour: arrosages.append(jour) or 0.0,
        fuseau=PARIS, maintenant=datetime(2026, 7, 14, 22, 30, tzinfo=UTC),   # 15 juillet, 0 h 30 à Paris
    )
    assert rapport.traites[0].bilan.date == date(2026, 7, 15)
    assert arrosages == [date(2026, 7, 15)]


def test_job_entre_minuit_et_2h_n_ecrase_pas_la_veille(client, db, meteo):
    headers = creer_compte(client)
    creer_espace(client, headers, reserve_utile_max=100, coefficient_cultural=1.0)
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=datetime(2026, 7, 14, 21, 0, tzinfo=UTC))
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=datetime(2026, 7, 14, 22, 30, tzinfo=UTC))

    bilans = db.query(BilanHydriqueJournalier).order_by(BilanHydriqueJournalier.date).all()
    assert [b.date for b in bilans] == [date(2026, 7, 14), date(2026, 7, 15)]
    assert [b.reserve_utile_fin_journee for b in bilans] == [95.0, 90.0]    # la veille est conservée


def test_arrosage_compte_sur_le_jour_local(client, db, meteo):
    headers = creer_compte(client)
    espace_id = creer_espace(client, headers, reserve_utile_max=100, coefficient_cultural=1.0)["id"]
    # 14 juillet 23 h UTC = 15 juillet 1 h à Paris ; 14 juillet 21 h UTC = 14 juillet 23 h à Paris
    db.add_all([
        ActionIrrigation(espace_id=espace_id, quantite_mm=3.0, timestamp=datetime(2026, 7, 14, 23, 0, tzinfo=UTC)),
        ActionIrrigation(espace_id=espace_id, quantite_mm=7.0, timestamp=datetime(2026, 7, 14, 21, 0, tzinfo=UTC)),
    ])
    db.commit()
    meteo.et0 = 20.0
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=datetime(2026, 7, 15, 8, 0, tzinfo=UTC))

    bilan = db.query(BilanHydriqueJournalier).one()
    assert bilan.date == date(2026, 7, 15)
    assert bilan.reserve_utile_fin_journee == 83.0          # 100 + 3 (arrosage du 15 local) − 20


def test_notification_critique_une_fois_par_jour_local(client, db, meteo):
    headers = creer_compte(client)
    creer_espace(client, headers, reserve_utile_max=10, coefficient_cultural=1.0)
    meteo.et0 = 9.0
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=datetime(2026, 7, 15, 6, 0, tzinfo=UTC))
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=datetime(2026, 7, 15, 20, 0, tzinfo=UTC))
    assert db.query(Notification).filter(Notification.type == "stress_hydrique").count() == 1


def test_fuseau_invalide_refuse(monkeypatch):
    from config import Settings
    monkeypatch.setenv("FUSEAU_HORAIRE", "Europe/Atlantide")
    with pytest.raises(RuntimeError, match="FUSEAU_HORAIRE"):
        Settings()


# --- Exposition réseau (non-régression du déploiement) -------------------------

def test_compose_publie_api_et_front_sur_l_interface_locale_par_defaut():
    compose = (RACINE / "docker-compose.yml").read_text(encoding="utf-8")
    assert '"${API_BIND:-127.0.0.1}:8000:8000"' in compose
    assert '"${FRONT_BIND:-127.0.0.1}:3000:80"' in compose
    assert "ENABLE_DOCS: ${ENABLE_DOCS:-false}" in compose


def test_uvicorn_croit_les_proxys_de_confiance_configures():
    dockerfile = (BACK_END / "Dockerfile").read_text(encoding="utf-8")
    assert "--proxy-headers" in dockerfile
    assert "--forwarded-allow-ips" in dockerfile and "TRUSTED_PROXIES:-127.0.0.1" in dockerfile
