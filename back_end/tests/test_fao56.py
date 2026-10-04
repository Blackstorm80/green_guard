"""Moteur hydrique FAO-56 paysager : calcul pur, rattrapage des jours manqués, historique et diagnostic."""
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest
import requests

from application.use_cases.generer_bilans_hydriques_journaliers import jours_a_rattraper
from config import settings
from domain.logic.bilan_hydrique import calculer_bilan_hydrique_pour_jour, epuisement_initial
from domain.logic.fao56 import (
    VERSION_MODELE,
    calculer_journee,
    coefficient_stress,
    eau_utile_texture,
    expliquer_bilan,
    pluie_efficace_mm,
    profondeur_racinaire_m,
    reserve_facilement_utilisable_mm,
    reserve_utile_totale_mm,
    statut_hydrique,
)
from domain.models import ActionIrrigation, BilanHydriqueJournalier, EspaceVert
from domain.ports.meteo import SERIE_JOURS_MAX, MeteoIndisponibleError
from infrastructure.jobs.mise_a_jour_capteurs import executer_mise_a_jour
from infrastructure.services import meteo_open_meteo
from infrastructure.services.meteo_open_meteo import OpenMeteoService
from tests.conftest import ajouter_membre, creer_compte, creer_espace

API = "/api/v1"
TAW_LIMON_GAZON = 46.5  # 0,155 m³/m³ × 0,3 m × 1000


def bilan_ferme(t) -> bool:
    attendu = t.epuisement_debut_mm - t.pluie_efficace_mm - t.arrosage_mm + t.etc_mm + t.drainage_mm
    return t.epuisement_fin_mm == pytest.approx(attendu)


# --- Réserve utile (TAW, RAW) ------------------------------------------------

def test_valeurs_de_reference_fao56_limon_30_cm():
    taw = reserve_utile_totale_mm("Limoneux", "Square")
    assert taw == pytest.approx(TAW_LIMON_GAZON)
    assert reserve_facilement_utilisable_mm(taw) == pytest.approx(23.25)
    assert reserve_utile_totale_mm("Limoneux", "Parc", profondeur_racinaire_cm=30) == pytest.approx(46.5)


@pytest.mark.parametrize("texture, eau_utile", [
    ("Sableux", 0.08), ("limoneux", 0.155), ("Limon-Argileux", 0.155), ("ARGILEUX", 0.16),
    ("argile", 0.16), (None, 0.14), ("tourbe", 0.14),
])
def test_eau_utile_par_texture(texture, eau_utile):
    assert eau_utile_texture(texture) == eau_utile


@pytest.mark.parametrize("profondeur_cm, type_espace, zr", [
    (None, "Square", 0.3), (None, "gazon", 0.3), (None, "Jardin", 0.4), (None, "Parc", 0.5),
    (None, "Rue", 0.8), (None, None, 0.4), (None, "Inconnu", 0.4), (0, "Parc", 0.5), (60, "Square", 0.6),
])
def test_profondeur_racinaire(profondeur_cm, type_espace, zr):
    assert profondeur_racinaire_m(profondeur_cm, type_espace) == pytest.approx(zr)


def test_reserve_saisie_prioritaire_sur_le_calcul():
    assert reserve_utile_totale_mm("Sableux", "Rue", reserve_saisie_mm=120) == 120
    assert reserve_utile_totale_mm("Sableux", "Rue", reserve_saisie_mm=None) == pytest.approx(64)


# --- Ks, statuts --------------------------------------------------------------

def test_coefficient_de_stress():
    taw, raw = TAW_LIMON_GAZON, 23.25
    assert coefficient_stress(0, taw, raw) == 1.0
    assert coefficient_stress(raw, taw, raw) == 1.0
    assert coefficient_stress(raw + (taw - raw) / 2, taw, raw) == pytest.approx(0.5)
    assert coefficient_stress(taw, taw, raw) == 0.0
    assert coefficient_stress(5, 0, 0) == 0.0                    # réserve nulle : pas de division par zéro


@pytest.mark.parametrize("epuisement, statut", [
    (0, "Optimal"), (23.25, "Optimal"), (23.3, "A surveiller"), (34.875, "A surveiller"),
    (34.9, "Critique"), (46.5, "Critique"),
])
def test_seuils_de_statut(epuisement, statut):
    assert statut_hydrique(epuisement, TAW_LIMON_GAZON, 23.25) == statut


def test_reserve_nulle_toujours_critique():
    t = calculer_journee(0, et0_mm=0, pluie_mm=0, arrosage_mm=0, taw_mm=0)
    assert (t.indice_stress, t.statut) == (1.0, "Critique")


# --- Journée de bilan ---------------------------------------------------------

def test_journee_sans_stress():
    t = calculer_journee(10, et0_mm=5, pluie_mm=0, arrosage_mm=0, taw_mm=TAW_LIMON_GAZON, kl=0.8)
    assert (t.ks, t.etc_mm, t.epuisement_fin_mm) == (1.0, pytest.approx(4.0), pytest.approx(14.0))
    assert t.reserve_restante_mm == pytest.approx(32.5)
    assert t.indice_stress == pytest.approx(14 / 46.5)
    assert bilan_ferme(t)


def test_ks_reduit_la_consommation_au_dela_de_raw():
    t = calculer_journee(30, et0_mm=5, pluie_mm=0, arrosage_mm=0, taw_mm=TAW_LIMON_GAZON, kl=0.8)
    assert t.ks == pytest.approx((46.5 - 30) / 23.25)
    assert t.etc_mm == pytest.approx(4 * t.ks)
    assert bilan_ferme(t)


def test_drainage_profond_quand_l_eau_depasse_la_capacite():
    t = calculer_journee(5, et0_mm=5, pluie_mm=20, arrosage_mm=3, taw_mm=TAW_LIMON_GAZON, kl=0.8)
    assert t.epuisement_fin_mm == 0
    assert t.drainage_mm == pytest.approx(20 + 3 - 5 - 4)        # conservé, et non perdu silencieusement
    assert t.statut == "Optimal" and bilan_ferme(t)


@pytest.mark.parametrize("pluie, efficace", [(0, 0), (1.9, 0), (2.0, 2.0), (12.5, 12.5)])
def test_petite_pluie_non_efficace(pluie, efficace):
    assert pluie_efficace_mm(pluie) == efficace
    t = calculer_journee(10, et0_mm=0, pluie_mm=pluie, arrosage_mm=0, taw_mm=TAW_LIMON_GAZON)
    assert t.pluie_mm == pluie and t.pluie_efficace_mm == efficace
    assert t.epuisement_fin_mm == pytest.approx(max(0, 10 - efficace))


def test_epuisement_borne_a_la_reserve_et_bilan_ferme():
    t = calculer_journee(9, et0_mm=100, pluie_mm=0, arrosage_mm=0, taw_mm=10, kl=1.0)
    assert t.epuisement_fin_mm == 10 and t.etc_mm == pytest.approx(1.0)
    assert t.indice_stress == 1.0 and t.statut == "Critique" and bilan_ferme(t)


def test_entrees_negatives_ignorees():
    t = calculer_journee(-3, et0_mm=-1, pluie_mm=-5, arrosage_mm=-2, taw_mm=TAW_LIMON_GAZON)
    assert (t.epuisement_debut_mm, t.etc_mm, t.pluie_mm, t.arrosage_mm, t.epuisement_fin_mm) == (0, 0, 0, 0, 0)


def ancien_modele_jours(et0: float, kc: float, seuil: float, ru_max: float = 100.0) -> int:
    """Ancien modèle (supprimé) : réserve 100 mm, consommation ET0 × Kc × facteur de sol (1 pour un limon),
    « A surveiller » dès un indice de stress de 0,3, « Critique » dès 0,6."""
    reserve, jour = ru_max, 0
    while 1 - reserve / ru_max < seuil:
        reserve, jour = max(0.0, reserve - et0 * kc), jour + 1
    return jour


def jours_avant(statuts: set[str], taw: float, et0: float, kl: float) -> int:
    epuisement, jour = 0.0, 0
    while True:
        jour += 1
        t = calculer_journee(epuisement, et0_mm=et0, pluie_mm=0, arrosage_mm=0, taw_mm=taw, kl=kl)
        epuisement = t.epuisement_fin_mm
        if t.statut in statuts:
            return jour


def test_comparaison_avec_l_ancien_modele_gazon_sur_limon():
    """Gazon sur limon (Square, Zr 0,3 m), ET0 4 mm/j sans pluie, même coefficient 0,8 dans les deux modèles.

    Ancien : « A surveiller » au jour 10, « Critique » au jour 19 (réserve fictive de 100 mm).
    FAO-56 : « A surveiller » au jour 8 (RAW épuisée), « Critique » au jour 12, malgré le freinage par Ks.
    """
    taw = reserve_utile_totale_mm("Limoneux", "Square")
    assert ancien_modele_jours(4, 0.8, 0.3) == 10
    assert ancien_modele_jours(4, 0.8, 0.6) == 19
    assert jours_avant({"A surveiller", "Critique"}, taw, 4, 0.8) == 8
    assert jours_avant({"Critique"}, taw, 4, 0.8) == 12


# --- Bilan d'un espace ----------------------------------------------------------

def espace_gazon(**champs):
    defaut = dict(id=1, type_sol="Limoneux", type_espace="Square", profondeur_racinaire=None,
                  reserve_utile_max=None, coefficient_cultural=0.8)
    return SimpleNamespace(**{**defaut, **champs})


def test_bilan_d_un_espace_conserve_tous_les_termes():
    bilan = calculer_bilan_hydrique_pour_jour(espace_gazon(), None, pluie_jour_mm=1.0, et0_jour_mm=5,
                                              arrosage_jour_mm=0, date_du_jour=date(2026, 7, 1),
                                              stress_sanitaire_jour=None, source_meteo="open-meteo")
    assert bilan.taw_mm == pytest.approx(46.5) and bilan.raw_mm == pytest.approx(23.25)
    assert (bilan.et0_mm, bilan.kl, bilan.ks, bilan.pluie_mm, bilan.pluie_efficace_mm) == (5, 0.8, 1.0, 1.0, 0)
    assert bilan.etc_mm == pytest.approx(4) and bilan.epuisement_fin_mm == pytest.approx(4)
    assert bilan.reserve_utile_fin_journee == pytest.approx(42.5)
    assert (bilan.version_modele, bilan.source_meteo) == (VERSION_MODELE, "open-meteo")


def test_epuisement_initial():
    assert epuisement_initial(None, 46.5) == 0
    assert epuisement_initial(SimpleNamespace(epuisement_fin_mm=12.0, indice_stress=0.9), 46.5) == 12
    assert epuisement_initial(SimpleNamespace(epuisement_fin_mm=80.0, indice_stress=0.9), 46.5) == 46.5
    # Bilan historique-v1 : la fraction consommée est reportée sur la TAW actuelle
    assert epuisement_initial(SimpleNamespace(epuisement_fin_mm=None, indice_stress=0.4), 50) == pytest.approx(20)


# --- Phrase explicative -------------------------------------------------------------

def jour(n, **champs):
    defaut = dict(date=date(2026, 7, n), taw_mm=50.0, epuisement_debut_mm=0.0, epuisement_fin_mm=0.0,
                  pluie_efficace_mm=0.0, etc_mm=4.0)
    return SimpleNamespace(**{**defaut, **champs})


def test_explication_depuis_la_derniere_pluie():
    historique = [jour(1, epuisement_fin_mm=20), jour(2, epuisement_fin_mm=15, pluie_efficace_mm=9),
                  jour(3, epuisement_fin_mm=24, etc_mm=4.2), jour(4, epuisement_fin_mm=33, etc_mm=4.6)]
    phrase = expliquer_bilan(historique)
    assert phrase == ("Réserve à 34 % : il a manqué 18 mm depuis la dernière pluie (9 mm, il y a 2 jours) ; "
                      "évapotranspiration de 4,2 mm/j.")


def test_explication_sans_pluie_et_pluie_du_jour():
    sec = [jour(1, epuisement_debut_mm=2, epuisement_fin_mm=6), jour(2, epuisement_fin_mm=10)]
    assert expliquer_bilan(sec) == "Réserve à 80 % : il a manqué 8 mm en 2 jour(s) sans pluie efficace ; " \
                                   "évapotranspiration de 4 mm/j."
    pluie = [jour(1, epuisement_fin_mm=6), jour(2, epuisement_fin_mm=0, pluie_efficace_mm=12.5)]
    assert expliquer_bilan(pluie).startswith("Réserve à 100 % : pluie efficace de 12,5 mm aujourd'hui")


def test_explication_absente_pour_un_bilan_historique():
    assert expliquer_bilan([]) is None
    assert expliquer_bilan([jour(1), jour(2, taw_mm=None, epuisement_fin_mm=None)]) is None


# --- Rattrapage des jours manqués -----------------------------------------------------

def a_8h(jour_: date) -> datetime:
    return datetime(jour_.year, jour_.month, jour_.day, 6, 0, tzinfo=UTC)   # 8 h à Paris en été


def bilans(db) -> list[BilanHydriqueJournalier]:
    db.expire_all()
    return db.query(BilanHydriqueJournalier).order_by(BilanHydriqueJournalier.date).all()


def test_jours_a_rattraper():
    assert jours_a_rattraper(None, date(2026, 7, 14)) == []
    assert jours_a_rattraper(date(2026, 7, 13), date(2026, 7, 14)) == []
    assert jours_a_rattraper(date(2026, 7, 10), date(2026, 7, 14)) == [date(2026, 7, d) for d in (11, 12, 13)]
    longs = jours_a_rattraper(date(2025, 1, 1), date(2026, 7, 14))
    assert len(longs) == SERIE_JOURS_MAX
    assert (longs[0], longs[-1]) == (date(2026, 7, 14) - timedelta(days=92), date(2026, 7, 13))


def test_rattrapage_de_trois_jours_manques_dans_l_ordre(client, db, meteo):
    headers = creer_compte(client)
    espace_id = creer_espace(client, headers, type_espace="Square", type_sol="Limoneux")["id"]
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=a_8h(date(2026, 7, 10)))
    # Le worker s'arrête trois jours ; un arrosage est saisi pendant la panne
    db.add(ActionIrrigation(espace_id=espace_id, quantite_mm=6.0, timestamp=datetime(2026, 7, 12, 10, tzinfo=UTC)))
    db.commit()
    meteo.serie = {date(2026, 7, 11): (6.0, 0.0), date(2026, 7, 12): (3.0, 15.0), date(2026, 7, 13): (5.0, 1.0)}

    executer_mise_a_jour(db, meteo_service=meteo, maintenant=a_8h(date(2026, 7, 14)))

    assert meteo.appels_serie == [(date(2026, 7, 11), date(2026, 7, 13))]
    lignes = bilans(db)
    assert [b.date.day for b in lignes] == [10, 11, 12, 13, 14]
    assert [b.et0_mm for b in lignes] == [5.0, 6.0, 3.0, 5.0, 5.0]
    assert [b.source_meteo for b in lignes] == ["test", "test-serie", "test-serie", "test-serie", "test"]
    assert lignes[2].arrosage_mm == 6.0 and lignes[2].pluie_efficace_mm == 15.0
    assert lignes[3].pluie_efficace_mm == 0.0                                 # 1 mm : non efficace
    for veille, jour_ in zip(lignes, lignes[1:], strict=False):              # chaîne continue, sans trou
        assert jour_.epuisement_debut_mm == pytest.approx(veille.epuisement_fin_mm)
    assert lignes[2].drainage_mm > 0                                           # 8,8 + 2,4 − 15 − 6 < 0 : excès drainé

    # Relance le même jour : rien à rattraper, bilan du jour remplacé (idempotence)
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=a_8h(date(2026, 7, 14)) + timedelta(hours=5))
    assert len(meteo.appels_serie) == 1
    assert [b.date.day for b in bilans(db)] == [10, 11, 12, 13, 14]


def test_rattrapage_limite_a_92_jours(client, db, meteo):
    headers = creer_compte(client)
    creer_espace(client, headers)
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=a_8h(date(2026, 1, 5)))
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=a_8h(date(2026, 7, 14)))

    debut, fin = meteo.appels_serie[0]
    assert (debut, fin) == (date(2026, 7, 14) - timedelta(days=92), date(2026, 7, 13))
    assert len(bilans(db)) == 1 + 92 + 1


def test_rattrapage_impossible_n_ecrit_rien_puis_reprend(client, db, meteo):
    headers = creer_compte(client)
    creer_espace(client, headers)
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=a_8h(date(2026, 7, 10)))

    meteo.serie_disponible = False
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=a_8h(date(2026, 7, 13)))
    assert [b.date.day for b in bilans(db)] == [10]          # ni jour courant enchaîné sur un trou

    meteo.serie_disponible, meteo.jours_absents = True, {date(2026, 7, 11)}
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=a_8h(date(2026, 7, 13)))
    assert [b.date.day for b in bilans(db)] == [10]          # série incomplète : même prudence

    meteo.jours_absents = set()
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=a_8h(date(2026, 7, 13)))
    assert [b.date.day for b in bilans(db)] == [10, 11, 12, 13]


def test_reprise_apres_un_bilan_historique(client, db, meteo):
    headers = creer_compte(client)
    espace_id = creer_espace(client, headers, reserve_utile_max=100, coefficient_cultural=1.0)["id"]
    db.add(BilanHydriqueJournalier(espace_id=espace_id, date=date(2026, 7, 13), reserve_utile_fin_journee=60,
                                   indice_stress=0.4, statut_hydrique="A surveiller", version_modele="historique-v1"))
    db.commit()
    executer_mise_a_jour(db, meteo_service=meteo, maintenant=a_8h(date(2026, 7, 14)))
    dernier = bilans(db)[-1]
    assert dernier.epuisement_debut_mm == pytest.approx(40) and dernier.epuisement_fin_mm == pytest.approx(45)
    assert dernier.version_modele == VERSION_MODELE


# --- API : réserve calculée, historique, lecture, diagnostic ---------------------------

def test_reserve_calculee_ou_saisie_par_l_espace(client):
    headers = creer_compte(client)
    espace = creer_espace(client, headers, type_espace="Square", type_sol="Limoneux")
    assert espace["reserve_utile_max"] is None
    assert espace["reserve_utile_effective_mm"] == pytest.approx(46.5)
    assert espace["coefficient_cultural"] == 0.8

    url = f"{API}/espaces-verts/{espace['id']}"
    assert client.put(url, json={"profondeur_racinaire": 50}, headers=headers).json()[
        "reserve_utile_effective_mm"] == pytest.approx(77.5)
    assert client.put(url, json={"reserve_utile_max": 80}, headers=headers).json()["reserve_utile_effective_mm"] == 80
    retour = client.put(url, json={"reserve_utile_max": None}, headers=headers).json()
    assert retour["reserve_utile_max"] is None and retour["reserve_utile_effective_mm"] == pytest.approx(77.5)


def ajouter_bilans(db, espace_id: int, jours: list[date]) -> None:
    for j in jours:
        db.add(BilanHydriqueJournalier(espace_id=espace_id, date=j, reserve_utile_fin_journee=40, indice_stress=0.2,
                                       statut_hydrique="Optimal", et0_mm=5, etc_mm=4, taw_mm=50, raw_mm=25,
                                       epuisement_debut_mm=6, epuisement_fin_mm=10, version_modele=VERSION_MODELE))
    db.commit()


def test_historique_des_bilans(client, db):
    headers = creer_compte(client)
    espace_id = creer_espace(client, headers)["id"]
    aujourd_hui = datetime.now(settings.fuseau).date()
    ajouter_bilans(db, espace_id, [aujourd_hui - timedelta(days=n) for n in (0, 1, 29, 30, 200)])

    url = f"{API}/espaces-verts/{espace_id}/bilans"
    defaut = client.get(url, headers=headers)
    assert defaut.status_code == 200
    assert [b["date"] for b in defaut.json()] == [
        (aujourd_hui - timedelta(days=n)).isoformat() for n in (29, 1, 0)]     # 30 jours, par date croissante
    premier = defaut.json()[0]
    assert (premier["taw_mm"], premier["etc_mm"], premier["version_modele"]) == (50, 4, VERSION_MODELE)
    assert len(client.get(url, params={"jours": 1}, headers=headers).json()) == 1
    assert len(client.get(url, params={"jours": 365}, headers=headers).json()) == 5
    for invalide in (0, 366, "abc"):
        assert client.get(url, params={"jours": invalide}, headers=headers).status_code == 422


def test_historique_des_bilans_droits_et_isolation(client, db):
    alice = creer_compte(client, "alice@example.com")
    espace_id = creer_espace(client, alice)["id"]
    ajouter_bilans(db, espace_id, [datetime.now(settings.fuseau).date()])
    url = f"{API}/espaces-verts/{espace_id}/bilans"

    lecteur = ajouter_membre(client, db, alice, "elu@example.com", "lecteur")
    assert client.get(url, headers=lecteur).status_code == 200            # consultation ouverte à tout membre
    bob = creer_compte(client, "bob@example.com")
    assert client.get(url, headers=bob).status_code == 404                # autre organisation
    assert client.get(f"{API}/espaces-verts/999999/bilans", headers=alice).status_code == 404
    client.cookies.clear()
    assert client.get(url).status_code == 401


def test_lecture_capteurs_et_diagnostic_avec_les_termes(client, db, meteo):
    headers = creer_compte(client)
    espace = creer_espace(client, headers, type_espace="Square", type_sol="Limoneux")
    vide = client.post(f"{API}/health/diagnostic", json={"espace_id": espace["id"]}, headers=headers).json()
    assert vide["statut"] == "Sans donnée" and vide["explication"] is None

    executer_mise_a_jour(db, meteo_service=meteo)
    lecture = client.get(f"{API}/capteurs/dashboard", headers=headers).json()["capteurs"][0]
    assert lecture["reserve_max_mm"] == 46.5 and lecture["reserve_facilement_utilisable_mm"] == 23.2
    assert lecture["reserve_eau_mm"] == 42.5 and lecture["reserve_percent"] == 91.4
    assert (lecture["et0_mm"], lecture["etc_mm"], lecture["version_modele"]) == (5.0, 4.0, VERSION_MODELE)

    diagnostic = client.post(f"{API}/health/diagnostic", json={"espace_id": espace["id"]}, headers=headers).json()
    assert diagnostic["statut"] == "Optimal"
    assert diagnostic["explication"] == ("Réserve à 91 % : il a manqué 4 mm en 1 jour(s) sans pluie efficace ; "
                                         "évapotranspiration de 4 mm/j.")


def test_humidite_simulee_suit_la_reserve_calculee(client, db, meteo):
    from domain.models import Mesure

    headers = creer_compte(client)
    creer_espace(client, headers, type_espace="Square", type_sol="Limoneux")
    executer_mise_a_jour(db, meteo_service=meteo)
    assert db.query(Mesure.humidite_sol).scalar() == pytest.approx(91.4)


def test_espace_entite_reserve_effective():
    assert EspaceVert(type_sol="Sableux", type_espace="Rue").reserve_utile_effective_mm == pytest.approx(64)
    assert EspaceVert(type_sol="Sableux", reserve_utile_max=30.0).reserve_utile_effective_mm == 30


# --- Série journalière Open-Meteo -----------------------------------------------------

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


def test_serie_journaliere_open_meteo(monkeypatch):
    appels = []

    def faux_get(url, params, timeout):
        appels.append(params)
        assert url == meteo_open_meteo.OPEN_METEO_URL and timeout == meteo_open_meteo.TIMEOUT_S
        return ReponseFictive({"daily": {
            "time": ["2026-07-10", "2026-07-11", "2026-07-12", "2026-07-13"],
            "et0_fao_evapotranspiration": [4.1, None, 5.3, 9.9],
            "precipitation_sum": [0.0, 3.2, None, 0.0],
        }})

    monkeypatch.setattr(meteo_open_meteo.requests, "get", faux_get)
    service = OpenMeteoService()
    serie = service.recuperer_serie_journaliere(45.76, 4.83, date(2026, 7, 10), date(2026, 7, 12))
    assert appels[0]["start_date"] == "2026-07-10" and appels[0]["end_date"] == "2026-07-12"
    assert appels[0]["timezone"] == "Europe/Paris"
    assert [(j.jour.day, j.et0_mm, j.pluie_mm) for j in serie] == [(10, 4.1, 0.0), (11, None, 3.2), (12, 5.3, 0.0)]
    assert {j.source for j in serie} == {"open-meteo"}

    service.recuperer_serie_journaliere(45.7601, 4.8301, date(2026, 7, 10), date(2026, 7, 12))
    assert len(appels) == 1                                                   # même point, même plage : cache


def test_serie_journaliere_bornee_et_erreurs(monkeypatch):
    service = OpenMeteoService()
    with pytest.raises(ValueError):
        service.recuperer_serie_journaliere(45.0, 4.0, date(2026, 7, 10), date(2026, 7, 9))
    with pytest.raises(ValueError):
        service.recuperer_serie_journaliere(45.0, 4.0, date(2026, 1, 1), date(2026, 1, 1) + timedelta(days=92))

    monkeypatch.setattr(meteo_open_meteo.requests, "get", lambda *a, **k: ReponseFictive({}, statut=503))
    with pytest.raises(MeteoIndisponibleError):
        service.recuperer_serie_journaliere(45.0, 4.0, date(2026, 7, 1), date(2026, 7, 3))
    monkeypatch.setattr(meteo_open_meteo.requests, "get", lambda *a, **k: ReponseFictive({"daily": {"x": []}}))
    with pytest.raises(MeteoIndisponibleError):
        service.recuperer_serie_journaliere(46.0, 5.0, date(2026, 7, 1), date(2026, 7, 3))
