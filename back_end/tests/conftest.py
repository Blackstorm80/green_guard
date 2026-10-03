import os
import tempfile
from datetime import datetime

import pytest

# Environnement de test fixé AVANT tout import applicatif (database.py et auth.py le lisent à l'import)
_DB_FILE = os.path.join(tempfile.mkdtemp(prefix="greenguard-tests-"), "test.db")
# TEST_DATABASE_URL permet de rejouer la suite sur PostgreSQL (CI) ; SQLite par défaut
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", f"sqlite:///{_DB_FILE}")
os.environ["SECRET_KEY"] = "cle-de-test-uniquement"
os.environ["ENABLE_SCHEDULER"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from api.v1.endpoints.meteo import get_meteo_service  # noqa: E402
from domain.ports.meteo import ConditionsMeteo, IMeteoService, MeteoIndisponibleError  # noqa: E402
from infrastructure.database import Base, SessionLocal, engine  # noqa: E402
from main import app  # noqa: E402

MOT_DE_PASSE = "motdepasse-solide-42"


class FausseMeteo(IMeteoService):
    """Météo déterministe : aucun appel réseau pendant les tests."""

    def __init__(self, et0: float = 5.0, pluie: float = 0.0, temperature: float = 22.0, disponible: bool = True):
        self.et0, self.pluie, self.temperature, self.disponible = et0, pluie, temperature, disponible
        self.appels = 0

    def recuperer_conditions_actuelles(self, latitude, longitude, maintenant: datetime) -> ConditionsMeteo:
        self.appels += 1
        if not self.disponible:
            raise MeteoIndisponibleError("indisponible")
        return ConditionsMeteo(
            city="Test", temperature_c=self.temperature, condition="Dégagé", ensoleillement_fort=True,
            humidite=55.0, pluie_jour_mm=self.pluie, et0_jour_mm=self.et0,
        )


@pytest.fixture(autouse=True)
def base_vierge():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
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


def creer_compte(client: TestClient, email: str = "alice@example.com") -> dict:
    """Inscrit puis connecte un utilisateur ; renvoie les en-têtes d'authentification."""
    r = client.post("/api/v1/auth/register", json={"name": "Alice", "email": email, "password": MOT_DE_PASSE})
    assert r.status_code == 201, r.text
    r = client.post("/api/v1/auth/login", data={"username": email, "password": MOT_DE_PASSE})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def creer_espace(client: TestClient, headers: dict, **champs) -> dict:
    payload = {"nom": "Parc Test", "latitude": 45.76, "longitude": 4.83, "surface_m2": 1000, **champs}
    r = client.post("/api/v1/espaces-verts/", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()
