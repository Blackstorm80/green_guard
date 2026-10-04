"""Couverture complémentaire : indicateurs végétaux (gestion), client Open-Meteo, notifications."""
from datetime import UTC, datetime

import pytest
import requests

from domain.models import Notification, User
from domain.ports.meteo import MeteoIndisponibleError
from infrastructure.jobs.mise_a_jour_capteurs import executer_mise_a_jour
from infrastructure.services import meteo_open_meteo
from infrastructure.services.meteo_open_meteo import OpenMeteoService
from tests.conftest import creer_compte, creer_espace

API = "/api/v1"


def changer_role(db, role, email="alice@example.com"):
    db.query(User).filter(User.email == email).update({User.role: role})
    db.commit()


def test_indicateurs_vegetaux_reserves_a_la_gestion(client, db, meteo):
    headers = creer_compte(client)
    creer_espace(client, headers, surface_m2=1000, reserve_utile_max=100, coefficient_cultural=1.0)
    changer_role(db, "technicien")
    assert client.get(f"{API}/vegetal/etat-global", headers=headers).status_code == 403

    changer_role(db, "gestionnaire")
    vide = client.get(f"{API}/vegetal/etat-global", headers=headers).json()
    assert vide["total_espaces"] == 1 and vide["espaces_en_stress"] == 0

    executer_mise_a_jour(db, meteo_service=meteo)
    etat = client.get(f"{API}/vegetal/etat-global", headers=headers).json()
    assert etat["sante_globale_percent"] == 95.0
    impact = client.get(f"{API}/vegetal/impact-carbone", headers=headers).json()
    assert impact["total_carbon_absorbed_kg"] > 0
    assert "× 365" in impact["periode"]
    assert impact["estimation_grossiere"] is True
    assert "Nowak" in impact["methode"]
    # 1000 m², stress 0,05 : ≈ 1,12 kg CO2/m²/an × 0,95 (et non plus ≈ 18 kg/m²/an)
    assert impact["total_carbon_absorbed_kg"] == pytest.approx(1000 * 0.306 * 44 / 12 * 0.95, abs=0.1)
    assert impact["detail_par_zone"][0]["carbon_kg"] == pytest.approx(impact["total_carbon_absorbed_kg"], abs=0.1)


def test_notification_marquee_lue_et_isolee(client, db):
    alice = creer_compte(client, "alice@example.com")
    bob = creer_compte(client, "bob@example.com")
    alice_id = db.query(User.id).filter(User.email == "alice@example.com").scalar()
    db.add(Notification(user_id=alice_id, message="Test", type="info"))
    db.commit()
    notif_id = client.get(f"{API}/notifications/", headers=alice).json()[0]["id"]

    assert client.post(f"{API}/notifications/{notif_id}/mark-as-read", headers=bob).status_code == 404
    r = client.post(f"{API}/notifications/{notif_id}/mark-as-read", headers=alice)
    assert r.status_code == 200 and r.json()["is_read"] is True


class ReponseFictive:
    def __init__(self, data, statut=200):
        self._data, self.status_code = data, statut

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def json(self):
        return self._data


@pytest.fixture(autouse=True)
def vider_cache_meteo():
    meteo_open_meteo._cache.clear()
    yield
    meteo_open_meteo._cache.clear()


def test_client_open_meteo_et_cache(monkeypatch):
    appels = []

    def faux_get(url, params, timeout):
        appels.append(params)
        assert timeout == meteo_open_meteo.TIMEOUT_S
        return ReponseFictive({
            "current": {"temperature_2m": 21.5, "relative_humidity_2m": 60, "cloud_cover": 10},
            "daily": {"et0_fao_evapotranspiration": [4.2], "precipitation_sum": [1.5]},
        })

    monkeypatch.setattr(meteo_open_meteo.requests, "get", faux_get)
    service = OpenMeteoService()
    maintenant = datetime.now(UTC)
    c = service.recuperer_conditions_actuelles(45.76, 4.83, maintenant)
    assert appels[0]["timezone"] == "Europe/Paris"            # jour météo = jour du bilan (FUSEAU_HORAIRE)
    assert (c.temperature_c, c.et0_jour_mm, c.pluie_jour_mm, c.ensoleillement_fort) == (21.5, 4.2, 1.5, True)

    service.recuperer_conditions_actuelles(45.7601, 4.8301, maintenant)   # même point arrondi → cache
    assert len(appels) == 1


def test_client_open_meteo_en_erreur(monkeypatch):
    monkeypatch.setattr(meteo_open_meteo.requests, "get", lambda *a, **k: ReponseFictive({}, statut=503))
    with pytest.raises(MeteoIndisponibleError):
        OpenMeteoService().recuperer_conditions_actuelles(45.0, 4.0, datetime.now(UTC))

    def coupure(*a, **k):
        raise requests.ConnectionError("réseau coupé")

    monkeypatch.setattr(meteo_open_meteo.requests, "get", coupure)
    with pytest.raises(MeteoIndisponibleError):
        OpenMeteoService().recuperer_conditions_actuelles(46.0, 5.0, datetime.now(UTC))
