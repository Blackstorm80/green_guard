import os
import tempfile
from datetime import date, datetime, timedelta

import pytest

# Environnement de test fixé AVANT tout import applicatif (database.py et auth.py le lisent à l'import)
_DB_FILE = os.path.join(tempfile.mkdtemp(prefix="greenguard-tests-"), "test.db")
# TEST_DATABASE_URL permet de rejouer la suite sur PostgreSQL (CI) ; SQLite par défaut
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", f"sqlite:///{_DB_FILE}")
os.environ["SECRET_KEY"] = "cle-de-test-uniquement-0123456789abcdef"
os.environ["ENABLE_SCHEDULER"] = "false"
# TestClient parle HTTP : un cookie Secure ne serait jamais renvoyé
os.environ["COOKIE_SECURE"] = "false"
os.environ["ENABLE_DOCS"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

from api.v1.endpoints.auth import limiteur_connexion, limiteur_inscription  # noqa: E402
from api.v1.endpoints.meteo import get_meteo_service  # noqa: E402
from domain.ports.meteo import (  # noqa: E402
    ConditionsMeteo,
    IMeteoService,
    MeteoIndisponibleError,
    MeteoJournaliere,
)
from infrastructure.database import Base, SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402

MOT_DE_PASSE = "motdepasse-solide-42"


class FausseMeteo(IMeteoService):
    """Météo déterministe : aucun appel réseau pendant les tests."""

    def __init__(self, et0: float = 5.0, pluie: float = 0.0, temperature: float = 22.0, disponible: bool = True):
        self.et0, self.pluie, self.temperature, self.disponible = et0, pluie, temperature, disponible
        self.appels = 0
        # Série passée (rattrapage) : valeurs par jour, sinon et0/pluie courants ; jours absents simulables
        self.serie: dict[date, tuple[float | None, float]] = {}
        self.jours_absents: set[date] = set()
        self.serie_disponible = True
        self.appels_serie: list[tuple[date, date]] = []

    def recuperer_conditions_actuelles(self, latitude, longitude, maintenant: datetime) -> ConditionsMeteo:
        self.appels += 1
        if not self.disponible:
            raise MeteoIndisponibleError("indisponible")
        return ConditionsMeteo(
            city="Test", temperature_c=self.temperature, condition="Dégagé", ensoleillement_fort=True,
            humidite=55.0, pluie_jour_mm=self.pluie, et0_jour_mm=self.et0, source="test",
        )

    def recuperer_serie_journaliere(self, latitude, longitude, debut: date, fin: date) -> list[MeteoJournaliere]:
        self.appels_serie.append((debut, fin))
        if not self.serie_disponible:
            raise MeteoIndisponibleError("indisponible")
        jours = (debut + timedelta(days=i) for i in range((fin - debut).days + 1))
        return [
            MeteoJournaliere(jour=j, et0_mm=self.serie.get(j, (self.et0, self.pluie))[0],
                             pluie_mm=self.serie.get(j, (self.et0, self.pluie))[1], source="test-serie")
            for j in jours if j not in self.jours_absents
        ]


@pytest.fixture(autouse=True)
def base_vierge():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    limiteur_connexion.reinitialiser()
    limiteur_inscription.reinitialiser()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def meteo():
    fausse = FausseMeteo()
    app.dependency_overrides[get_meteo_service] = lambda: fausse
    return fausse


@pytest.fixture
def client(meteo):
    return TestClient(app)


def connecter(client: TestClient, email: str) -> dict:
    r = client.post("/api/v1/auth/login", data={"username": email, "password": MOT_DE_PASSE})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def creer_compte(client: TestClient, email: str = "alice@example.com", **champs) -> dict:
    """Inscrit (nouvelle organisation, rôle admin) puis connecte un utilisateur ; renvoie les en-têtes."""
    r = client.post("/api/v1/auth/register",
                    json={"name": "Alice", "email": email, "password": MOT_DE_PASSE, **champs})
    assert r.status_code == 201, r.text
    return connecter(client, email)


def ajouter_membre(client: TestClient, db, headers_admin: dict, email: str, role: str) -> dict:
    """Ajoute un membre à l'organisation de l'admin (en base : l'invitation n'existe pas encore)."""
    from api.deps.auth import get_password_hash
    from domain.models import User

    organisation_id = client.get("/api/v1/users/me", headers=headers_admin).json()["organisation"]["id"]
    db.add(User(name=email.split("@")[0], email=email, hashed_password=get_password_hash(MOT_DE_PASSE),
                organisation_id=organisation_id, role=role))
    db.commit()
    return connecter(client, email)


def creer_espace(client: TestClient, headers: dict, **champs) -> dict:
    payload = {"nom": "Parc Test", "latitude": 45.76, "longitude": 4.83, "surface_m2": 1000, **champs}
    r = client.post("/api/v1/espaces-verts/", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()
