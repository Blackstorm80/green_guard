"""Prévision à 7 jours : projection de la réserve, date de bascule, décision arroser / reporter / surveiller / rien."""
import os
import tempfile
from datetime import UTC, date, datetime, timedelta

import pytest
import requests
from sqlalchemy import create_engine, text

from alembic import command
from api.v1.endpoints.meteo import get_meteo_service
from config import settings
from domain.logic.fao56 import VERSION_MODELE
from domain.logic.prevision import (
    ARROSER,
    REPORTER,
    RIEN,
    SURVEILLER,
    EtatHydrique,
    PrevisionImpossibleError,
    PrevisionMeteoIncompleteError,
    formater_jour,
    pluie_acquise,
    pluie_comptee_mm,
    premiere_bascule,
    prevoir,
    projeter_reserve,
)
from domain.models import BilanHydriqueJournalier, Mesure, Notification
from domain.ports.meteo import MeteoIndisponibleError, PrevisionJournaliere
from infrastructure.jobs.mise_a_jour_capteurs import TYPE_ARROSAGE_A_PREVOIR, executer_mise_a_jour
from infrastructure.services import meteo_open_meteo
from infrastructure.services.meteo_open_meteo import OpenMeteoService
from main import app
from tests.conftest import ajouter_membre, creer_compte, creer_espace
from tests.test_migrations import config_alembic

API = "/api/v1"
TAW, RAW = 46.5, 23.25            # square sur limon (Zr 0,3 m) ; Critique au-delà de 34,875 mm
J = date(2026, 7, 13)             # un lundi


def prevision(et0: float = 5.0, pluies: dict[int, tuple[float, float | None]] | None = None,
              debut: date = J, jours: int = 8) -> list[PrevisionJournaliere]:
    """Prévision de debut à debut + jours - 1 ; pluies[décalage] = (cumul, probabilité)."""
    pluies = pluies or {}
    return [PrevisionJournaliere(debut + timedelta(days=i), et0, *pluies.get(i, (0.0, 0.0)), source="test")
            for i in range(jours)]


def etat(epuisement: float, jour: date = J) -> EtatHydrique:
    return EtatHydrique(date=jour, epuisement_mm=epuisement, taw_mm=TAW, kl=0.8, et0_mm=5.0, pluie_mm=0.0)


# --- Domaine : règle de la pluie comptée -----------------------------------------------------

@pytest.mark.parametrize("pluie, probabilite, acquise", [
    (5.0, 70, True), (12.0, 95, True), (4.9, 100, False), (20.0, 69, False), (20.0, None, False), (0.0, 100, False),
])
def test_pluie_acquise_seulement_probable_et_suffisante(pluie, probabilite, acquise):
    assert pluie_acquise(pluie, probabilite) is acquise


@pytest.mark.parametrize("decalage, pluie, probabilite, comptee", [
    (0, 3.0, None, 3.0),       # aujourd'hui : cumul du jour, comme le bilan
    (1, 12.0, 80, 12.0),       # demain : acquise, comptée en entier
    (1, 12.0, 30, 0.0),        # demain : peu probable, non comptée
    (1, 4.0, 100, 0.0),        # demain : trop faible pour être acquise
    (2, 20.0, 50, 0.0),        # J+2 (fenêtre de la consigne) : seulement probable, non comptée
    (2, 20.0, 80, 20.0),       # J+2 : acquise, comptée en entier
    (3, 20.0, 50, 10.0),       # au-delà : pondérée par la probabilité
    (5, 10.0, None, 0.0),      # probabilité inconnue : rien
    (3, 10.0, 10, 1.0),
])
def test_pluie_comptee_selon_l_echeance(decalage, pluie, probabilite, comptee):
    assert pluie_comptee_mm(decalage, pluie, probabilite) == pytest.approx(comptee)


def test_formater_jour_en_francais():
    assert formater_jour(J) == "lundi 13 juillet"
    assert formater_jour(date(2026, 10, 8)) == "jeudi 8 octobre"


# --- Domaine : scénarios chiffrés --------------------------------------------------------------

def test_sans_pluie_bascule_calculee_puis_surveiller():
    """Dr 20 mm, ET0 5, KL 0,8 : « A surveiller » dès J+1 (24 mm), Critique à J+5 (35,9 mm)."""
    p = prevoir(etat(20.0), prevision(), J)
    assert [j.jour for j in p.jours] == [J + timedelta(days=i) for i in range(8)]
    assert p.jours[0].issu_du_bilan and p.jours[0].reserve_mm == pytest.approx(26.5)
    epuisements = [round(j.epuisement_fin_mm, 2) for j in p.jours]
    assert epuisements[:6] == [20.0, 24.0, 27.87, 31.08, 33.73, 35.93]
    assert p.date_bascule_a_surveiller == J + timedelta(days=1)
    assert p.date_bascule_critique == J + timedelta(days=5)
    assert p.decision.code == SURVEILLER and p.decision.date_limite is None
    assert p.decision.texte == "Critique prévu le samedi 18 juillet : à surveiller (prévision indicative)."
    assert [j.indicatif for j in p.jours] == [False] * 4 + [True] * 4


def test_bascule_a_j2_arroser_au_plus_tard_la_veille_avec_la_dose():
    """Dr 30 mm : 32,84 mm à J+1, Critique à J+2 (35,19 mm) ; arroser au plus tard J+1."""
    p = prevoir(etat(30.0), prevision(), J, surface_m2=1000, type_irrigation="Aspersion", debit_l_min=100)
    assert p.date_bascule_critique == J + timedelta(days=2)
    assert p.decision.code == ARROSER
    assert p.decision.date_limite == J + timedelta(days=1)
    # Dose au jour limite : Dr 32,84 mm × 1 000 m² / 0,75
    assert p.decision.dose.mm == 32.8
    assert p.decision.dose.litres == pytest.approx(43785, abs=1)
    assert p.decision.dose.minutes == 438
    assert p.decision.texte.startswith(
        "Arroser au plus tard le mardi 14 juillet : critique prévu le mercredi 15 juillet.")
    assert "Pour remplir la réserve : 32,8 mm, soit 43 785 L (438 min" in p.decision.texte


def test_deja_critique_arroser_des_aujourd_hui():
    p = prevoir(etat(40.0), prevision(), J, surface_m2=100, type_irrigation="Manuel")
    assert p.date_bascule_critique == J and p.date_bascule_a_surveiller == J
    assert p.decision.code == ARROSER and p.decision.date_limite == J
    assert p.decision.texte.startswith("Arroser dès aujourd'hui : la réserve est critique.")
    assert p.decision.dose.mm == 40.0


def test_critique_demain_arroser_aujourd_hui():
    p = prevoir(etat(34.0), prevision(), J)
    assert p.date_bascule_critique == J + timedelta(days=1)
    assert p.decision.code == ARROSER and p.decision.date_limite == J
    assert p.decision.texte.startswith("Arroser aujourd'hui au plus tard : critique prévu demain (mardi 14 juillet).")
    assert p.decision.dose.litres is None                                   # surface inconnue


def test_pluie_acquise_dans_les_48h_reporter():
    """Dr 30 mm ; 12 mm à 80 % demain : la réserve tient jusque-là et la pluie la remonte (20,8 mm)."""
    p = prevoir(etat(30.0), prevision(pluies={1: (12.0, 80)}), J)
    assert p.decision.code == REPORTER
    assert p.decision.jour_pluie == J + timedelta(days=1) and p.decision.pluie_attendue_mm == 12.0
    assert p.decision.texte == "Reporter l'arrosage : pluie de 12 mm attendue demain (probabilité 80 %)."
    assert p.jours[1].pluie_acquise and p.jours[1].pluie_comptee_mm == 12.0
    assert p.jours[1].epuisement_fin_mm == pytest.approx(30 - 12 + 4 * (TAW - 30) / (TAW - RAW))


def test_pluie_acquise_a_j2_annoncee_par_son_jour():
    p = prevoir(etat(31.0), prevision(pluies={2: (15.0, 90)}), J)
    assert p.decision.code == REPORTER
    assert p.decision.texte == "Reporter l'arrosage : pluie de 15 mm attendue mercredi 15 juillet (probabilité 90 %)."


def test_pluie_peu_probable_non_comptee_arroser():
    sec = prevoir(etat(30.0), prevision(), J)
    p = prevoir(etat(30.0), prevision(pluies={1: (12.0, 30), 3: (10.0, 10)}), J)
    assert not p.jours[1].pluie_acquise and p.jours[1].pluie_comptee_mm == 0.0
    assert p.jours[3].pluie_comptee_mm == pytest.approx(1.0)               # pondérée mais sous 2 mm : inefficace
    assert [j.epuisement_fin_mm for j in p.jours] == [j.epuisement_fin_mm for j in sec.jours]
    assert p.decision.code == ARROSER


def test_pluie_acquise_trop_tard_arroser_quand_meme():
    """Dr 34 mm : Critique dès demain ; la pluie acquise de J+2 arrive trop tard pour reporter."""
    p = prevoir(etat(34.0), prevision(pluies={2: (10.0, 90)}), J)
    assert p.decision.code == ARROSER and p.decision.date_limite == J


def test_pluie_acquise_insuffisante_apres_coup_arroser():
    """Canicule (ET0 7) : Dr 33 mm, 5 mm à 70 % demain. La pluie remonte la réserve à J+1 (31,25 mm)
    mais l'espace passe Critique dès J+2 (34,92 mm) : arroser au plus tard J+1, pas de report."""
    p = prevoir(etat(33.0), prevision(et0=7.0, pluies={1: (5.0, 70)}), J)
    assert [round(j.epuisement_fin_mm, 2) for j in p.jours[:3]] == [33.0, 31.25, 34.92]
    assert p.date_bascule_critique == J + timedelta(days=2)
    assert p.decision.code == ARROSER and p.decision.date_limite == J + timedelta(days=1)
    assert p.decision.texte.startswith("Arroser au plus tard le mardi 14 juillet : critique prévu le mercredi")


def test_pluie_acquise_ne_fait_gagner_qu_un_jour_reporter_en_le_disant():
    """ET0 10 : Dr 34,69 mm à J+1 ; 5 mm acquis à J+2 maintiennent la réserve (33,76 mm), Critique à J+3."""
    p = prevoir(etat(28.5), prevision(et0=10.0, pluies={2: (5.0, 70)}), J)
    assert p.jours[2].pluie_acquise and p.jours[2].pluie_comptee_mm == 5.0
    assert p.jours[2].statut == "A surveiller" and p.date_bascule_critique == J + timedelta(days=3)
    assert p.decision.code == REPORTER
    assert p.decision.texte == ("Reporter l'arrosage : pluie de 5 mm attendue mercredi 15 juillet (probabilité 70 %)."
                                " Critique prévu ensuite le jeudi 16 juillet : à surveiller.")


@pytest.mark.parametrize("pluie, probabilite", [(15.0, 60), (20.0, 69), (4.0, 100)])
def test_pluie_non_acquise_a_j2_ne_supprime_pas_la_consigne(pluie, probabilite):
    """Dr 30 mm, ET0 5 : Critique à J+2 sans pluie. Une pluie seulement probable (ou trop faible) à J+2
    n'est pas comptée : arroser au plus tard J+1, exactement comme par temps sec."""
    sec = prevoir(etat(30.0), prevision(), J)
    p = prevoir(etat(30.0), prevision(pluies={2: (pluie, probabilite)}), J)
    assert p.jours[2].pluie_comptee_mm == 0.0 and not p.jours[2].pluie_acquise
    assert [j.epuisement_fin_mm for j in p.jours] == [j.epuisement_fin_mm for j in sec.jours]
    assert p.date_bascule_critique == J + timedelta(days=2)
    assert p.decision.code == ARROSER and p.decision.date_limite == J + timedelta(days=1)


def test_decision_reporter_jamais_avec_une_bascule_dans_la_fenetre():
    """Cohérence API : « reporter » n'est jamais renvoyé avec un Critique prévu à J+2 ou avant."""
    reports = 0
    for epuisement in (26.0, 28.0, 30.0, 32.0, 33.0, 34.0):
        for et0 in (4.0, 6.0, 8.0):
            for jour_pluie in (1, 2):
                for cumul, proba in ((5.0, 70), (8.0, 90), (15.0, 75)):
                    p = prevoir(etat(epuisement), prevision(et0=et0, pluies={jour_pluie: (cumul, proba)}), J)
                    if p.decision.code == REPORTER:
                        reports += 1
                        assert p.date_bascule_critique is None or p.date_bascule_critique > J + timedelta(days=2)
    assert reports > 0


def test_pluie_ponderee_au_dela_de_j1():
    p = prevoir(etat(10.0), prevision(pluies={4: (20.0, 50)}), J)
    assert p.jours[4].pluie_comptee_mm == 10.0 and not p.jours[4].pluie_acquise
    assert p.jours[4].epuisement_fin_mm == pytest.approx(p.jours[3].epuisement_fin_mm - 10 + 4)


def test_aucune_bascule_rien():
    p = prevoir(etat(0.0), prevision(et0=2.0), J)
    assert max(j.epuisement_fin_mm for j in p.jours) == pytest.approx(11.2)
    assert p.date_bascule_critique is None and p.date_bascule_a_surveiller is None
    assert p.decision.code == RIEN and p.decision.texte == "Aucun besoin d'arrosage prévu sur 7 jours."


def test_rien_mais_reserve_a_surveiller_annoncee():
    p = prevoir(etat(20.0), prevision(et0=1.5), J)
    assert p.date_bascule_critique is None
    assert p.decision.code == RIEN
    assert p.decision.texte.endswith("Réserve « à surveiller » à partir du jeudi 16 juillet.")


def test_depart_du_bilan_de_la_veille_projette_aujourd_hui():
    p = prevoir(etat(20.0, jour=J - timedelta(days=1)), prevision(pluies={0: (3.0, 100)}), J)
    assert len(p.jours) == 8 and not p.jours[0].issu_du_bilan
    # Aujourd'hui projeté avec le cumul du jour (3 mm, efficace) : 20 − 3 + 4
    assert p.jours[0].epuisement_fin_mm == pytest.approx(21.0)


def test_bilan_trop_ancien_ou_prevision_incomplete():
    with pytest.raises(PrevisionImpossibleError, match="trop ancien"):
        prevoir(etat(20.0, jour=J - timedelta(days=2)), prevision(), J)
    with pytest.raises(PrevisionMeteoIncompleteError):
        prevoir(etat(20.0), prevision(jours=6), J)
    trouee = prevision()
    trouee[3] = PrevisionJournaliere(J + timedelta(days=3), None, 0.0, 0.0)
    with pytest.raises(PrevisionMeteoIncompleteError):
        projeter_reserve(etat(20.0), trouee, J)


def test_premiere_bascule_sans_jours():
    assert premiere_bascule([], "Critique") is None


# --- Service Open-Meteo : prévision, cache, panne ----------------------------------------------

class ReponseFictive:
    def __init__(self, data, statut=200):
        self._data, self.status_code = data, statut

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def json(self):
        return self._data


def reponse_prevision(debut: date = J, jours: int = 8) -> dict:
    return {"daily": {
        "time": [(debut + timedelta(days=i)).isoformat() for i in range(jours)],
        "et0_fao_evapotranspiration": [4.0 + i / 10 for i in range(jours)],
        "precipitation_sum": [None] + [float(i) for i in range(1, jours)],
        "precipitation_probability_max": [None, 80] + [10] * (jours - 2),
    }}


@pytest.fixture(autouse=True)
def vider_cache_meteo():
    meteo_open_meteo._cache.clear()
    yield
    meteo_open_meteo._cache.clear()


def test_prevision_open_meteo_parametres_et_lecture(monkeypatch):
    appels = []

    def faux_get(url, params, timeout):
        appels.append(params)
        assert url == meteo_open_meteo.OPEN_METEO_URL and timeout == meteo_open_meteo.TIMEOUT_S
        return ReponseFictive(reponse_prevision())

    monkeypatch.setattr(meteo_open_meteo.requests, "get", faux_get)
    service = OpenMeteoService()
    jours = service.recuperer_prevision_journaliere(45.76, 4.83)
    assert appels[0]["daily"] == "et0_fao_evapotranspiration,precipitation_sum,precipitation_probability_max"
    assert appels[0]["forecast_days"] == 8                                  # J (aujourd'hui) puis J+1..J+7
    assert appels[0]["timezone"] == "Europe/Paris"
    assert [(j.jour, j.et0_mm, j.pluie_mm, j.probabilite_pluie_pct) for j in jours[:2]] == [
        (J, 4.0, 0.0, None), (J + timedelta(days=1), 4.1, 1.0, 80)]
    assert {j.source for j in jours} == {"open-meteo"}

    service.recuperer_prevision_journaliere(45.7601, 4.8301)                # même point arrondi → cache
    assert len(appels) == 1


def test_prevision_open_meteo_panne_memorisee(monkeypatch):
    appels = []

    def panne(*a, **k):
        appels.append(1)
        raise requests.ConnectionError("réseau coupé")

    monkeypatch.setattr(meteo_open_meteo.requests, "get", panne)
    service = OpenMeteoService()
    for _ in range(3):
        with pytest.raises(MeteoIndisponibleError):
            service.recuperer_prevision_journaliere(45.0, 4.0)
    assert len(appels) == 1                       # échec mémorisé : pas un délai d'attente par lecture

    # L'échec expire : le service est de nouveau interrogé
    cle = next(c for c in meteo_open_meteo._cache if c[:3] == (45.0, 4.0, "prevision"))
    meteo_open_meteo._cache[cle] = (0.0, meteo_open_meteo._cache[cle][1])
    monkeypatch.setattr(meteo_open_meteo.requests, "get", lambda *a, **k: ReponseFictive(reponse_prevision()))
    assert len(service.recuperer_prevision_journaliere(45.0, 4.0)) == 8


def test_prevision_open_meteo_reponse_illisible(monkeypatch):
    monkeypatch.setattr(meteo_open_meteo.requests, "get", lambda *a, **k: ReponseFictive({"daily": {"x": []}}))
    with pytest.raises(MeteoIndisponibleError):
        OpenMeteoService().recuperer_prevision_journaliere(46.0, 5.0)
    monkeypatch.setattr(meteo_open_meteo.requests, "get", lambda *a, **k: ReponseFictive({}, statut=429))
    with pytest.raises(MeteoIndisponibleError):
        OpenMeteoService().recuperer_prevision_journaliere(47.0, 5.0)


def test_prevision_open_meteo_cache_change_de_jour_a_minuit(monkeypatch):
    """Une prévision mise en cache à 23 h 55 (J-1..J+6 après minuit) n'est pas resservie le lendemain."""
    appels = []
    horloge = {"maintenant": datetime(2026, 7, 12, 21, 55, tzinfo=UTC)}     # 23 h 55 à Paris

    class Horloge(datetime):
        @classmethod
        def now(cls, tz=None):
            return horloge["maintenant"].astimezone(tz)

    def faux_get(url, params, timeout):
        appels.append(params)
        return ReponseFictive(reponse_prevision(debut=Horloge.now(meteo_open_meteo.ZoneInfo("Europe/Paris")).date()))

    monkeypatch.setattr(meteo_open_meteo, "datetime", Horloge)
    monkeypatch.setattr(meteo_open_meteo.requests, "get", faux_get)
    service = OpenMeteoService()
    assert service.recuperer_prevision_journaliere(45.0, 4.0)[0].jour == J - timedelta(days=1)
    horloge["maintenant"] = datetime(2026, 7, 12, 22, 5, tzinfo=UTC)          # 00 h 05 à Paris
    jours = service.recuperer_prevision_journaliere(45.0, 4.0)
    assert len(appels) == 2 and jours[0].jour == J
    projeter_reserve(etat(20.0), jours, J)                                   # couvre bien J..J+7


@pytest.mark.parametrize("champ, valeur", [
    ("et0_fao_evapotranspiration", "4,2"), ("et0_fao_evapotranspiration", float("nan")),
    ("precipitation_sum", -3.0), ("precipitation_sum", True), ("precipitation_probability_max", 140),
    ("precipitation_probability_max", float("inf")),
])
def test_prevision_open_meteo_valeur_aberrante_inexploitable(monkeypatch, champ, valeur):
    data = reponse_prevision()
    data["daily"][champ][2] = valeur
    monkeypatch.setattr(meteo_open_meteo.requests, "get", lambda *a, **k: ReponseFictive(data))
    with pytest.raises(MeteoIndisponibleError, match="inexploitable"):
        OpenMeteoService().recuperer_prevision_journaliere(48.0, 2.0)
    assert not any(c[:2] == (48.0, 2.0) and not isinstance(v[1], meteo_open_meteo._Echec)
                   for c, v in meteo_open_meteo._cache.items())              # rien d'aberrant en cache


def test_cache_meteo_purge_les_entrees_expirees(monkeypatch):
    monkeypatch.setattr(meteo_open_meteo, "CACHE_MAX_ENTREES", 3)
    for i in range(3):
        meteo_open_meteo._cache[("vieux", i)] = (0.0, "expiré")
        meteo_open_meteo._verrous_par_point[("vieux", i)] = meteo_open_meteo.Lock()
    meteo_open_meteo._ecrire_cache(("neuf",), "frais", 60)
    assert list(meteo_open_meteo._cache) == [("neuf",)]
    assert not any(c[0] == "vieux" for c in meteo_open_meteo._verrous_par_point)


# --- API ---------------------------------------------------------------------------------------

def aujourd_hui() -> date:
    return datetime.now(settings.fuseau).date()


def espace_avec_bilan(client, db, headers, epuisement: float, **champs) -> dict:
    """Square sur limon (TAW 46,5 mm) avec un bilan FAO-56 du jour à l'épuisement donné."""
    espace = creer_espace(client, headers, type_espace="Square", type_sol="Limoneux", **champs)
    db.add(BilanHydriqueJournalier(
        espace_id=espace["id"], date=aujourd_hui(), reserve_utile_fin_journee=TAW - epuisement,
        indice_stress=epuisement / TAW, statut_hydrique="A surveiller", epuisement_debut_mm=epuisement - 3,
        epuisement_fin_mm=epuisement, et0_mm=5, kl=0.8, ks=1, etc_mm=3, pluie_mm=0, pluie_efficace_mm=0,
        arrosage_mm=0, drainage_mm=0, taw_mm=TAW, raw_mm=RAW, version_modele=VERSION_MODELE,
    ))
    db.commit()
    return espace


def test_prevision_d_un_espace(client, db, meteo):
    alice = creer_compte(client)
    espace = espace_avec_bilan(client, db, alice, 30.0, surface_m2=1000, type_irrigation="Aspersion")
    r = client.get(f"{API}/espaces-verts/{espace['id']}/prevision", headers=alice)
    assert r.status_code == 200, r.text
    corps = r.json()
    j = aujourd_hui()
    assert corps["date_calcul"] == corps["date_bilan"] == j.isoformat()
    assert corps["reserve_max_mm"] == TAW
    assert len(corps["jours"]) == 8 and corps["jours"][0]["issu_du_bilan"] is True
    assert corps["jours"][0]["reserve_mm"] == 16.5
    assert {"jour", "reserve_mm", "statut", "et0_mm", "pluie_mm", "probabilite_pluie_pct",
            "pluie_comptee_mm", "pluie_acquise", "indicatif"} <= set(corps["jours"][1])
    assert corps["date_bascule_critique"] == (j + timedelta(days=2)).isoformat()
    assert corps["decision"]["code"] == "arroser"
    assert corps["decision"]["date_limite"] == (j + timedelta(days=1)).isoformat()
    assert corps["decision"]["dose_recommandee"] == {"mm": 32.8, "litres": 43785.0, "minutes": None}
    assert "indicative au-delà de J+3" in corps["avertissement"]
    assert corps["source_meteo"] == "test-prevision"


def test_prevision_reporter_par_l_api(client, db, meteo):
    alice = creer_compte(client)
    espace = espace_avec_bilan(client, db, alice, 30.0)
    meteo.prevision = {1: (5.0, 12.0, 85.0)}
    decision = client.get(f"{API}/espaces-verts/{espace['id']}/prevision", headers=alice).json()["decision"]
    assert decision["code"] == "reporter" and decision["pluie_attendue_mm"] == 12.0
    assert decision["dose_recommandee"] is None


def test_prevision_sans_bilan_ou_sans_meteo(client, db, meteo):
    alice = creer_compte(client)
    sans_bilan = creer_espace(client, alice)
    r = client.get(f"{API}/espaces-verts/{sans_bilan['id']}/prevision", headers=alice)
    assert r.status_code == 409 and "aucun bilan hydrique récent" in r.json()["detail"]

    espace = espace_avec_bilan(client, db, alice, 30.0)
    meteo.prevision_disponible = False
    r = client.get(f"{API}/espaces-verts/{espace['id']}/prevision", headers=alice)
    assert r.status_code == 502 and r.json()["detail"] == "Service météo momentanément indisponible."


def test_prevision_bilan_historique_non_exploitable(client, db, meteo):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    db.add(BilanHydriqueJournalier(espace_id=espace["id"], date=aujourd_hui(), reserve_utile_fin_journee=40,
                                   indice_stress=0.6, statut_hydrique="A surveiller", version_modele="historique-v1"))
    db.commit()
    assert client.get(f"{API}/espaces-verts/{espace['id']}/prevision", headers=alice).status_code == 409


def test_prevision_isolation_et_droits(client, db, meteo):
    alice = creer_compte(client)
    espace = espace_avec_bilan(client, db, alice, 30.0)
    url = f"{API}/espaces-verts/{espace['id']}/prevision"
    client.cookies.clear()
    assert client.get(url).status_code == 401
    bob = creer_compte(client, "bob@example.com")
    assert client.get(url, headers=bob).status_code == 404               # autre organisation : pas de fuite
    assert client.get(f"{API}/espaces-verts/999999/prevision", headers=alice).status_code == 404
    lecteur = ajouter_membre(client, db, alice, "elu@example.com", "lecteur")
    assert client.get(url, headers=lecteur).status_code == 200            # lecture : tout membre
    # Le tableau de bord de Bob ne porte aucune prévision des espaces d'Alice
    assert client.get(f"{API}/capteurs/dashboard", headers=bob).json()["capteurs"] == []


def lecture(client, headers, espace_id: int) -> dict:
    capteurs = client.get(f"{API}/capteurs/dashboard", headers=headers).json()["capteurs"]
    return next(c for c in capteurs if c["espace_id"] == espace_id)


def test_tableau_de_bord_expose_decision_et_date_de_bascule(client, db, meteo):
    alice = creer_compte(client)
    arroser = espace_avec_bilan(client, db, alice, 30.0, surface_m2=100)
    tranquille = espace_avec_bilan(client, db, alice, 2.0, nom="Square calme")
    sans_bilan = creer_espace(client, alice, nom="Nouveau")

    lu = lecture(client, alice, arroser["id"])
    assert lu["decision"]["code"] == "arroser"
    assert lu["date_bascule"] == (aujourd_hui() + timedelta(days=2)).isoformat()
    assert lu["decision"]["dose_recommandee"]["litres"] == 4378.0          # Dr 32,84 mm × 100 m² / 0,75
    assert lecture(client, alice, tranquille["id"])["decision"]["code"] in ("rien", "surveiller")
    vide = lecture(client, alice, sans_bilan["id"])
    assert vide["decision"] is None and vide["date_bascule"] is None
    # Jour métier du serveur : référence du front pour situer la date de bascule
    assert client.get(f"{API}/capteurs/dashboard", headers=alice).json()["date_calcul"] == aujourd_hui().isoformat()


def test_contrat_decision_visible_dans_openapi(client):
    schema = client.get("/openapi.json").json()["components"]["schemas"]["DecisionDTO"]
    assert schema["properties"]["code"]["enum"] == ["arroser", "reporter", "surveiller", "rien"]


def test_tableau_de_bord_fonctionne_malgre_une_prevision_inattendue(client, db, meteo):
    """Une donnée inattendue du fournisseur prive l'espace de décision, pas l'organisation de tableau de bord."""
    alice = creer_compte(client)
    espace_avec_bilan(client, db, alice, 30.0)
    meteo.prevision = {3: ("abc", 0.0, 0.0)}
    r = client.get(f"{API}/capteurs/dashboard", headers=alice)
    assert r.status_code == 200
    assert r.json()["capteurs"][0]["decision"] is None


def test_tableau_de_bord_fonctionne_sans_meteo_prevue(client, db, meteo):
    alice = creer_compte(client)
    for i in range(3):
        espace_avec_bilan(client, db, alice, 30.0, nom=f"Espace {i}", latitude=43.0 + i, longitude=1.0 + i)
    meteo.prevision_disponible = False
    r = client.get(f"{API}/capteurs/dashboard", headers=alice)
    assert r.status_code == 200
    assert [c["decision"] for c in r.json()["capteurs"]] == [None, None, None]
    assert r.json()["metrics"]["espaces_suivis"] == 3
    assert len(meteo.appels_prevision) == 1          # panne générale : les points suivants ne sont pas interrogés


def test_tableau_de_bord_un_seul_appel_meteo_pour_deux_espaces_voisins(client, db, monkeypatch):
    """Service réel (réseau simulé) : deux espaces à moins d'1 km partagent la prévision mise en cache."""
    alice = creer_compte(client)
    espace_avec_bilan(client, db, alice, 30.0, latitude=45.7601, longitude=4.8301)
    espace_avec_bilan(client, db, alice, 10.0, nom="Voisin", latitude=45.7612, longitude=4.8344)
    appels = []

    def faux_get(url, params, timeout):
        appels.append(params)
        if "current" in params:
            return ReponseFictive({"current": {"temperature_2m": 20, "relative_humidity_2m": 50, "cloud_cover": 10},
                                   "daily": {"et0_fao_evapotranspiration": [5.0], "precipitation_sum": [0.0]}})
        return ReponseFictive(reponse_prevision(debut=aujourd_hui()))

    monkeypatch.setattr(meteo_open_meteo.requests, "get", faux_get)
    app.dependency_overrides[get_meteo_service] = OpenMeteoService
    capteurs = client.get(f"{API}/capteurs/dashboard", headers=alice).json()["capteurs"]
    assert all(c["decision"] is not None for c in capteurs)
    assert len([a for a in appels if "forecast_days" in a and a["forecast_days"] == 8]) == 1


# --- Worker : notification « Arrosage à prévoir » -----------------------------------------------

def espace_a_arroser_bientot(client, db, headers, **champs) -> dict:
    """Bilan de la veille à 28 mm : 31,2 mm aujourd'hui (A surveiller), Critique à J+2 sans pluie."""
    espace = creer_espace(client, headers, type_espace="Square", type_sol="Limoneux", **champs)
    db.add(BilanHydriqueJournalier(
        espace_id=espace["id"], date=aujourd_hui() - timedelta(days=1), reserve_utile_fin_journee=TAW - 28,
        indice_stress=28 / TAW, statut_hydrique="A surveiller", epuisement_debut_mm=25, epuisement_fin_mm=28,
        et0_mm=5, kl=0.8, etc_mm=3, pluie_mm=0, pluie_efficace_mm=0, arrosage_mm=0, drainage_mm=0,
        taw_mm=TAW, raw_mm=RAW, version_modele=VERSION_MODELE,
    ))
    db.commit()
    return espace


def alertes(db, type_: str = TYPE_ARROSAGE_A_PREVOIR) -> list[Notification]:
    db.expire_all()
    return db.query(Notification).filter_by(type=type_).order_by(Notification.id).all()


def test_worker_notifie_l_arrosage_a_prevoir_une_fois_par_jour(client, db, meteo):
    alice = creer_compte(client)
    ajouter_membre(client, db, alice, "elu@example.com", "lecteur")
    technicien = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    espace = espace_a_arroser_bientot(client, db, alice, nom="Square Gare", surface_m2=100)

    executer_mise_a_jour(db, meteo_service=meteo)
    notes = alertes(db)
    assert len(notes) == 2                                 # admin et technicien ; le lecteur n'est pas alerté
    assert {n.espace_id for n in notes} == {espace["id"]}
    limite = formater_jour(aujourd_hui() + timedelta(days=1))
    assert notes[0].message.startswith(f"Arrosage à prévoir sur « Square Gare » au plus tard le {limite}.")
    assert "Pour remplir la réserve" in notes[0].message
    assert alertes(db, "stress_hydrique") == []

    # Passage horaire suivant, même si la date limite a changé : pas de second message dans la journée
    meteo.prevision = {2: (5.0, 0.0, 0.0), 1: (7.0, 0.0, 0.0)}
    executer_mise_a_jour(db, meteo_service=meteo)
    assert len(alertes(db)) == 2
    lues = client.get(f"{API}/users/me/notifications", headers=technicien).json()
    assert lues[0]["type"] == TYPE_ARROSAGE_A_PREVOIR and lues[0]["espace_id"] == espace["id"]


def test_worker_pas_d_alerte_si_report_ou_meteo_prevue_absente(client, db, meteo):
    alice = creer_compte(client)
    espace_a_arroser_bientot(client, db, alice)
    meteo.prevision = {1: (5.0, 15.0, 90.0)}                # pluie acquise demain : reporter
    executer_mise_a_jour(db, meteo_service=meteo)
    assert alertes(db) == []

    meteo.prevision, meteo.prevision_disponible = {}, False
    executer_mise_a_jour(db, meteo_service=meteo)
    assert alertes(db) == []
    db.expire_all()
    assert db.query(BilanHydriqueJournalier).filter_by(date=aujourd_hui()).count() == 1   # bilan tout de même


def test_worker_espace_deja_critique_une_seule_alerte(client, db, meteo):
    alice = creer_compte(client)
    espace = creer_espace(client, alice, type_espace="Square", type_sol="Limoneux")
    db.add(BilanHydriqueJournalier(
        espace_id=espace["id"], date=aujourd_hui() - timedelta(days=1), reserve_utile_fin_journee=TAW - 40,
        indice_stress=40 / TAW, statut_hydrique="Critique", epuisement_fin_mm=40, taw_mm=TAW, raw_mm=RAW, kl=0.8,
        version_modele=VERSION_MODELE,
    ))
    db.commit()
    executer_mise_a_jour(db, meteo_service=meteo)
    assert alertes(db) == []
    critiques = alertes(db, "stress_hydrique")
    assert len(critiques) == 1 and critiques[0].espace_id == espace["id"]


def test_worker_isolation_des_alertes(client, db, meteo):
    """Deux organisations ayant chacune un espace à arroser : chaque alerte reste dans la sienne."""
    alice = creer_compte(client)
    bob = creer_compte(client, "bob@example.com")
    carole = creer_compte(client, "carole@example.com")                    # sans espace : rien
    espace_alice = espace_a_arroser_bientot(client, db, alice, nom="Square Alice")
    espace_bob = espace_a_arroser_bientot(client, db, bob, nom="Square Bob")
    executer_mise_a_jour(db, meteo_service=meteo)
    assert len(alertes(db)) == 2
    for headers, espace, nom in ((alice, espace_alice, "Square Alice"), (bob, espace_bob, "Square Bob")):
        notes = [n for n in client.get(f"{API}/users/me/notifications", headers=headers).json()
                 if n["type"] == TYPE_ARROSAGE_A_PREVOIR]
        assert len(notes) == 1
        assert notes[0]["espace_id"] == espace["id"] and f"« {nom} »" in notes[0]["message"]
    assert client.get(f"{API}/users/me/notifications", headers=carole).json() == []


def test_worker_echec_inattendu_de_la_prevision_n_annule_pas_le_reste(client, db, meteo):
    """Une erreur imprévue de la prévision ne fait pas perdre bilans, mesures et alertes de stress."""
    alice = creer_compte(client)
    espace_a_arroser_bientot(client, db, alice)
    critique = creer_espace(client, alice, nom="Critique", type_espace="Square", type_sol="Limoneux")
    db.add(BilanHydriqueJournalier(
        espace_id=critique["id"], date=aujourd_hui() - timedelta(days=1), reserve_utile_fin_journee=TAW - 40,
        indice_stress=40 / TAW, statut_hydrique="Critique", epuisement_fin_mm=40, taw_mm=TAW, raw_mm=RAW, kl=0.8,
        version_modele=VERSION_MODELE,
    ))
    db.commit()
    meteo.prevision = {3: ("abc", 0.0, 0.0)}                                # TypeError dans le moteur
    executer_mise_a_jour(db, meteo_service=meteo)
    db.expire_all()
    assert db.query(BilanHydriqueJournalier).filter_by(date=aujourd_hui()).count() == 2
    assert db.query(Mesure).count() == 2
    assert len(alertes(db, "stress_hydrique")) == 1 and alertes(db) == []


def test_suppression_de_l_espace_conserve_la_notification(client, db, meteo):
    alice = creer_compte(client)
    espace = espace_a_arroser_bientot(client, db, alice)
    executer_mise_a_jour(db, meteo_service=meteo)
    assert client.delete(f"{API}/espaces-verts/{espace['id']}", headers=alice).status_code == 204
    notes = alertes(db)
    assert len(notes) == 1 and notes[0].espace_id is None


# --- Migration 0005 ------------------------------------------------------------------------------

def test_migration_rattache_les_alertes_existantes_a_leur_espace(monkeypatch):
    url = f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'prevision.db')}"
    config = config_alembic(monkeypatch, url)
    command.upgrade(config, "0004_boucle_arrosage")
    engine = create_engine(url)
    message = "Stress hydrique critique sur « {} » : arrosage recommandé."
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO organisations (id, nom, slug) VALUES (1, 'A', 'a'), (2, 'B', 'b')"))
        conn.execute(text(
            "INSERT INTO users (id, name, email, hashed_password, organisation_id, role) VALUES "
            "(1, 'Ana', 'ana@example.com', 'h', 1, 'admin'), (2, 'Ben', 'ben@example.com', 'h', 2, 'admin')"
        ))
        conn.execute(text(
            "INSERT INTO espaces_verts (id, nom, latitude, longitude, organisation_id) VALUES "
            "(10, 'Parc', 45.7, 4.8, 1), (11, 'Parc', 45.7, 4.8, 2), (12, 'Double', 45.7, 4.8, 2), "
            "(13, 'Double', 45.8, 4.9, 2)"
        ))
        conn.execute(text("INSERT INTO notifications (id, user_id, type, message) VALUES "
                          "(1, 1, 'stress_hydrique', :parc), (2, 2, 'stress_hydrique', :parc), "
                          "(3, 2, 'stress_hydrique', :double), (4, 1, 'info', 'Bonjour')"),
                     {"parc": message.format("Parc"), "double": message.format("Double")})

    command.upgrade(config, "head")
    with engine.begin() as conn:
        rattachees = conn.execute(text("SELECT id, espace_id FROM notifications ORDER BY id")).all()
        # Chaque alerte vers l'espace de l'organisation du destinataire ; nom ambigu : laissée sans espace
        assert [tuple(r) for r in rattachees] == [(1, 10), (2, 11), (3, None), (4, None)]

    command.downgrade(config, "0004_boucle_arrosage")
    with engine.begin() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM notifications")).scalar() == 4
    engine.dispose()


def test_maintenant_explicite_du_tableau_de_bord():
    """Le jour de calcul suit le fuseau métier : 23 h 30 UTC le 13 juillet = 14 juillet à Paris."""
    from application.use_cases.capteurs import obtenir_dashboard_capteurs
    from tests.conftest import FausseMeteo

    class AucunCapteur:
        def lectures_actuelles(self, espaces):
            return []

    meteo = FausseMeteo()
    dto = obtenir_dashboard_capteurs([], AucunCapteur(), meteo, settings.fuseau,
                                     maintenant=datetime(2026, 7, 13, 23, 30, tzinfo=UTC))
    assert dto.statut == "En attente" and meteo.appels_prevision == []
