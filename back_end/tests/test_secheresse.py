"""Mode sécheresse VigiEau : client, règles, refus des arrosages interdits, registre, état, isolation."""
import csv
import io
import os
import tempfile
from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace

import pytest
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from application.use_cases import secheresse as module_secheresse
from config import settings
from domain.logic.arrosage import DoseRecommandee
from domain.logic.fao56 import VERSION_MODELE
from domain.logic.prevision import ARROSER, REPORTER, Decision
from domain.logic.secheresse import (
    ALERTE,
    ALERTE_RENFORCEE,
    AUCUNE,
    CRISE,
    INCONNU,
    INTERDIT,
    PRIORITE_ARBRES,
    PRIORITE_AUTRES,
    PRIORITE_JEUNES_PLANTATIONS,
    PRIORITE_MASSIFS,
    RECUPERATION,
    VIGILANCE,
    ReglesSecheresse,
    ajouter_annees,
    appliquer_restriction,
    evaluer_arrosage,
    jeune_plantation,
    parametres_depuis_regles,
    plage_autorisee,
    priorite_secheresse,
    regles_depuis_parametres,
)
from domain.models import BilanHydriqueJournalier, EspaceVert, Intervention, Notification, RestrictionSecheresse, User
from domain.ports.vigieau import NiveauVigieau, VigieauIndisponibleError, VigieauInjoignableError
from infrastructure.jobs.mise_a_jour_capteurs import executer_mise_a_jour
from infrastructure.repositories.restriction_secheresse_repository_impl import RestrictionSecheresseRepositoryImpl
from infrastructure.services import vigieau as module_vigieau
from infrastructure.services.vigieau import VigieauService
from tests.conftest import ajouter_membre, creer_compte, creer_espace
from tests.test_migrations import config_alembic

API = "/api/v1"
J = date(2026, 7, 15)
DEFAUT = ReglesSecheresse()


# --- Règles (domaine pur) ----------------------------------------------------------------------

@pytest.mark.parametrize(("heure", "autorise"), [
    (time(12), False), (time(11), False), (time(17, 59), False), (time(19), True), (time(18), True), (time(8), True),
])
def test_alerte_interdit_de_11_h_a_18_h(heure, autorise):
    evaluation = evaluer_arrosage(ALERTE, DEFAUT, J, heure)
    assert evaluation.autorise is autorise
    assert evaluation.interdit_toute_la_journee is False
    assert evaluation.plage_interdite == "11:00–18:00"
    assert ("interdit de 11 h à 18 h" in evaluation.motif) is not autorise


@pytest.mark.parametrize("niveau", [CRISE, ALERTE_RENFORCEE])
def test_crise_et_alerte_renforcee_interdisent_toute_la_journee(niveau):
    for heure in (time(6), time(12), time(22), None):
        evaluation = evaluer_arrosage(niveau, DEFAUT, J, heure)
        assert evaluation.autorise is False and evaluation.interdit_toute_la_journee is True
        assert evaluation.derogation is None
    assert "Arrosage interdit" in evaluer_arrosage(CRISE, DEFAUT, J).motif


@pytest.mark.parametrize("niveau", [AUCUNE, VIGILANCE])
def test_aucune_restriction_et_vigilance_autorisent(niveau):
    evaluation = evaluer_arrosage(niveau, DEFAUT, J, time(14))
    assert evaluation.autorise is True and evaluation.plage_interdite is None


def test_motif_de_plage_interdite_en_francais():
    assert evaluer_arrosage(ALERTE, DEFAUT, J, time(12)).motif.startswith(
        "Arrosage interdit de 11 h à 18 h : niveau alerte")
    jeune = evaluer_arrosage(CRISE, DEFAUT, J, time(12), date_plantation=J - timedelta(days=30))
    assert jeune.motif.endswith("l'arrosage est interdit de 11 h à 18 h.")
    regles = regles_depuis_parametres({"secheresse": {"niveaux": {
        "alerte": {"interdit": False, "plage_interdite": {"debut": "08:30", "fin": "20:00"}}}}})
    assert "interdit de 8 h 30 à 20 h" in evaluer_arrosage(ALERTE, regles, J, time(12)).motif
    assert "–" not in evaluer_arrosage(ALERTE, DEFAUT, J, time(12)).motif


def test_niveau_inconnu_ne_bloque_pas_mais_avertit():
    evaluation = evaluer_arrosage(None, DEFAUT, J, time(14))
    assert evaluation.niveau == INCONNU and evaluation.autorise is True
    assert "inconnu" in evaluation.motif
    assert evaluer_arrosage("niveau-farfelu", DEFAUT, J).niveau == INCONNU


def test_derogation_jeune_plantation_hors_plage():
    plantation = J - timedelta(days=365)
    soir = evaluer_arrosage(CRISE, DEFAUT, J, time(19), date_plantation=plantation)
    assert soir.autorise is True and soir.derogation == "Jeune plantation de moins de 2 ans"
    assert soir.plage_interdite == "11:00–18:00"
    midi = evaluer_arrosage(CRISE, DEFAUT, J, time(12), date_plantation=plantation)
    assert midi.autorise is False and "même par dérogation" in midi.motif
    # Plantation de plus de 2 ans, ou plantée dans le futur : pas de dérogation
    assert evaluer_arrosage(CRISE, DEFAUT, J, time(19), date_plantation=J - timedelta(days=800)).autorise is False
    assert evaluer_arrosage(CRISE, DEFAUT, J, time(19), date_plantation=J + timedelta(days=3)).autorise is False


def test_derogation_eau_de_recuperation_sans_plage():
    evaluation = evaluer_arrosage(CRISE, DEFAUT, J, time(12), source_eau=RECUPERATION)
    assert evaluation.autorise is True and evaluation.plage_interdite is None
    assert "récupération" in evaluation.derogation
    # En alerte aussi, la plage ne s'applique pas à l'eau de récupération
    assert evaluer_arrosage(ALERTE, DEFAUT, J, time(12), source_eau=RECUPERATION).autorise is True


def test_derogations_desactivables():
    regles = ReglesSecheresse(jeunes_plantations_ans=None, eau_recuperation=False)
    assert evaluer_arrosage(CRISE, regles, J, time(19), source_eau=RECUPERATION).autorise is False
    assert evaluer_arrosage(CRISE, regles, J, time(19), date_plantation=J - timedelta(days=30)).autorise is False


def test_regles_parametrables_et_aller_retour_json():
    parametres = {"secheresse": {
        "niveaux": {"alerte": {"interdit": False, "plage_interdite": {"debut": "08:00", "fin": "20:00"}},
                    "alerte_renforcee": {"interdit": False, "plage_interdite": {"debut": "09:00", "fin": "20:00"}}},
        "derogations": {"jeunes_plantations_ans": 3, "plage_interdite_jeunes_plantations": None,
                        "eau_recuperation": False},
    }}
    regles = regles_depuis_parametres(parametres)
    assert evaluer_arrosage(ALERTE, regles, J, time(19)).autorise is False
    assert evaluer_arrosage(ALERTE_RENFORCEE, regles, J, time(21)).autorise is True
    assert evaluer_arrosage(CRISE, regles, J, time(12)).autorise is False          # crise : défaut conservé
    jeune = evaluer_arrosage(CRISE, regles, J, time(12), date_plantation=J - timedelta(days=900))
    assert jeune.autorise is True and jeune.derogation == "Jeune plantation de moins de 3 ans"
    assert regles_depuis_parametres({"secheresse": parametres_depuis_regles(regles)}) == regles
    assert regles_depuis_parametres(None) == DEFAUT
    # Paramètres illisibles (saisie directe en base) : les défauts s'appliquent, jamais aucune règle
    assert regles_depuis_parametres({"secheresse": {"niveaux": {"alerte": {"plage_interdite": "x"}}}}) == DEFAUT


def test_regle_incomplete_en_base_garde_les_defauts_du_guide():
    # Une clé absente ne lève jamais une interdiction : chaque champ manquant prend le défaut du guide
    regles = regles_depuis_parametres({"secheresse": {"niveaux": {"crise": {}, "alerte": {"interdit": False}},
                                                      "derogations": {"jeunes_plantations_ans": 2}}})
    assert regles == DEFAUT
    jeune = J - timedelta(days=100)
    assert evaluer_arrosage(CRISE, regles, J, time(12), date_plantation=jeune).autorise is False
    assert evaluer_arrosage(CRISE, regles, J, time(12)).autorise is False
    assert evaluer_arrosage(ALERTE, regles, J, time(12)).autorise is False


@pytest.mark.parametrize("derogations", [
    {"jeunes_plantations_ans": "2"}, {"jeunes_plantations_ans": True}, {"jeunes_plantations_ans": -1},
    {"jeunes_plantations_ans": float("nan")}, {"jeunes_plantations_ans": 50}, {"eau_recuperation": "false"},
])
def test_derogation_de_type_illisible_en_base_retombe_sur_les_defauts(derogations):
    # Saisie directe en base : jamais d'erreur 500 à l'évaluation, jamais une dérogation accordée par erreur
    regles = regles_depuis_parametres({"secheresse": {"derogations": derogations}})
    assert regles == DEFAUT
    assert evaluer_arrosage(CRISE, regles, J, time(20), date_plantation=J - timedelta(days=100)).autorise is True
    assert regles_depuis_parametres({"secheresse": {"niveaux": {"crise": {"interdit": "non"}}}}) == DEFAUT


def test_jeune_plantation_au_calendrier():
    # Deuxième anniversaire sans 29 février dans l'intervalle (730 jours) : la dérogation a pris fin
    plantation = date(2025, 3, 1)
    assert jeune_plantation(plantation, date(2027, 2, 28), DEFAUT) is True
    assert jeune_plantation(plantation, date(2027, 3, 1), DEFAUT) is False
    assert jeune_plantation(plantation, plantation, DEFAUT) is True
    assert ajouter_annees(date(2024, 2, 29), 2) == date(2026, 2, 28)
    assert ajouter_annees(date(2025, 1, 1), 1.5) == date(2026, 7, 3)        # 1 an + 183 jours
    assert jeune_plantation(date(2024, 2, 29), date(2026, 2, 28),
                            ReglesSecheresse(jeunes_plantations_ans=2)) is False


def test_priorite_de_l_eau():
    assert priorite_secheresse("Parc", J - timedelta(days=100), J, DEFAUT) == PRIORITE_JEUNES_PLANTATIONS
    assert priorite_secheresse("Rue", None, J, DEFAUT) == PRIORITE_ARBRES
    assert priorite_secheresse("Jardin", J - timedelta(days=2000), J, DEFAUT) == PRIORITE_MASSIFS
    assert priorite_secheresse("Square", None, J, DEFAUT) == PRIORITE_AUTRES
    assert PRIORITE_JEUNES_PLANTATIONS < PRIORITE_ARBRES < PRIORITE_MASSIFS < PRIORITE_AUTRES


def test_plage_autorisee_du_registre():
    assert plage_autorisee(ALERTE, "11:00–18:00") == "hors 11:00–18:00"
    assert plage_autorisee(AUCUNE, None) == "toute la journée"
    assert plage_autorisee(INCONNU, None) == "non vérifiée (niveau inconnu)"


def _arroser() -> Decision:
    return Decision(ARROSER, "Arroser au plus tard le jeudi 16 juillet : critique prévu le vendredi 17 juillet.",
                    date_limite=J + timedelta(days=1), dose=DoseRecommandee(30.0, 4000.0, 40.0))


def test_decision_interdite_sans_dose_en_crise():
    decision = appliquer_restriction(_arroser(), evaluer_arrosage(CRISE, DEFAUT, J), J)
    assert decision.code == INTERDIT and decision.dose is None
    assert decision.texte.startswith("Arrosage interdit") and "jeudi 16 juillet" in decision.texte


def test_decision_arroser_hors_plage_en_alerte():
    decision = appliquer_restriction(_arroser(), evaluer_arrosage(ALERTE, DEFAUT, J), J)
    assert decision.code == ARROSER and decision.dose is not None
    assert decision.texte.endswith("Arroser hors 11 h–18 h (alerte).")
    assert decision.plage_interdite == "11:00–18:00"
    jeune = evaluer_arrosage(CRISE, DEFAUT, J, date_plantation=J - timedelta(days=200))
    decision = appliquer_restriction(_arroser(), jeune, J)
    assert decision.code == ARROSER and "dérogation : jeune plantation" in decision.texte
    assert decision.derogation == "Jeune plantation de moins de 2 ans"


def test_decision_inchangee_hors_arrosage_ou_sans_restriction():
    reporter = Decision(REPORTER, "Reporter l'arrosage.")
    assert appliquer_restriction(reporter, evaluer_arrosage(CRISE, DEFAUT, J), J) == reporter
    assert appliquer_restriction(_arroser(), None, J) == _arroser()
    assert appliquer_restriction(_arroser(), evaluer_arrosage(AUCUNE, DEFAUT, J), J).texte == _arroser().texte


# --- Client VigiEau (réponses simulées) --------------------------------------------------------

class FausseReponse:
    def __init__(self, status_code=200, donnees=None, json_invalide=False):
        self.status_code, self.donnees, self.json_invalide = status_code, donnees, json_invalide

    def json(self):
        if self.json_invalide:
            raise ValueError("pas du JSON")
        return self.donnees


def _zone(niveau: str, type_: str = "AEP", **champs) -> dict:
    return {"id": 1, "nom": f"Zone {type_}", "code": "69_0004", "type": type_, "niveauGravite": niveau,
            "departement": "69", "arrete": {"id": 37857, "cheminFichier": "https://regleau.example/arrete.pdf"},
            "usages": [], **champs}


@pytest.fixture
def appels_http(monkeypatch):
    module_vigieau.vider_cache()
    appels = []
    reponse = {"valeur": FausseReponse(200, [])}

    def faux_get(url, params=None, timeout=None, allow_redirects=True, headers=None):
        appels.append({"url": url, "params": params, "timeout": timeout, "allow_redirects": allow_redirects})
        if isinstance(reponse["valeur"], Exception):
            raise reponse["valeur"]
        return reponse["valeur"]

    monkeypatch.setattr(module_vigieau.requests, "get", faux_get)
    yield appels, reponse
    module_vigieau.vider_cache()


@pytest.mark.parametrize("niveau", ["vigilance", "alerte", "alerte_renforcee", "crise"])
def test_client_lit_chaque_niveau(appels_http, niveau):
    appels, reponse = appels_http
    reponse["valeur"] = FausseReponse(200, [_zone(niveau, "SOU")])
    resultat = VigieauService().niveau_au_point(45.764, 4.8357, "SOU")
    assert resultat.niveau == niveau and resultat.type_zone == "SOU"
    assert resultat.zone_nom == "Zone SOU" and resultat.arrete_identifiant == "37857"
    assert resultat.arrete_url == "https://regleau.example/arrete.pdf"
    appel = appels[0]
    assert appel["url"] == settings.vigieau_url and appel["allow_redirects"] is False
    assert appel["params"] == {"lon": "4.835700", "lat": "45.764000", "profil": "collectivite", "zoneType": "SOU"}
    assert appel["timeout"] == settings.vigieau_timeout_s


def test_client_aucune_restriction(appels_http):
    appels, reponse = appels_http
    assert VigieauService().niveau_au_point(45.0, 4.0, "AEP").niveau == AUCUNE
    # Entrée « arrêté municipal » seule (sans niveau) : aucune zone d'alerte
    reponse["valeur"] = FausseReponse(200, [{"id": None, "type": "AEP", "arreteMunicipalCheminFichier": "x"}])
    assert VigieauService().niveau_au_point(47.0, 4.0, "AEP").niveau == AUCUNE


def test_client_sans_type_retient_la_zone_la_plus_severe(appels_http):
    appels, reponse = appels_http
    reponse["valeur"] = FausseReponse(200, [_zone("alerte", "SUP"), _zone("crise", "AEP"), _zone("vigilance", "SOU")])
    resultat = VigieauService().niveau_au_point(45.0, 4.0, None)
    assert (resultat.niveau, resultat.type_zone) == ("crise", "AEP")
    assert "zoneType" not in appels[0]["params"]


@pytest.mark.parametrize("reponse_simulee", [
    FausseReponse(500, {"message": "Plusieurs zones"}), FausseReponse(400, {}), FausseReponse(200, json_invalide=True),
    FausseReponse(200, {"pas": "une liste"}), FausseReponse(200, [_zone("rouge")]), FausseReponse(200, ["texte"]),
])
def test_client_reponse_inexploitable(appels_http, reponse_simulee):
    _, reponse = appels_http
    reponse["valeur"] = reponse_simulee
    with pytest.raises(VigieauIndisponibleError):
        VigieauService().niveau_au_point(45.0, 4.0, "AEP")


@pytest.mark.parametrize("statut", [502, 503, 504])
def test_client_passerelle_en_panne_jamais_aucune_restriction(appels_http, statut):
    _, reponse = appels_http
    reponse["valeur"] = FausseReponse(statut, {"message": "Bad Gateway", "statusCode": statut})
    with pytest.raises(VigieauInjoignableError):
        VigieauService().niveau_au_point(45.0, 4.0, "AEP")


def test_client_404_erreur_du_point_jamais_aucune_restriction(appels_http):
    # VIGIEAU_URL mal saisie (« Cannot GET ») ou 404 « aucune zone » du README : jamais « aucune restriction »,
    # mais pas une panne générale qui couperait l'actualisation des espaces suivants
    _, reponse = appels_http
    reponse["valeur"] = FausseReponse(404, {"message": "Aucune zone d'alerte en vigueur", "statusCode": 404})
    with pytest.raises(VigieauIndisponibleError) as erreur:
        VigieauService().niveau_au_point(45.0, 4.0, "AEP")
    assert not isinstance(erreur.value, VigieauInjoignableError)


def test_client_api_indisponible_puis_echec_memorise(appels_http):
    appels, reponse = appels_http
    reponse["valeur"] = requests.Timeout("délai dépassé")
    with pytest.raises(VigieauInjoignableError):
        VigieauService().niveau_au_point(45.0, 4.0, "AEP")
    with pytest.raises(VigieauInjoignableError):
        VigieauService().niveau_au_point(45.0, 4.0, "AEP")
    assert len(appels) == 1                       # pas un second délai d'attente dans la minute


def test_client_cache_par_point_et_par_jour(appels_http):
    appels, reponse = appels_http
    reponse["valeur"] = FausseReponse(200, [_zone("alerte")])
    service = VigieauService()
    service.niveau_au_point(45.0, 4.0, "AEP")
    service.niveau_au_point(45.0, 4.0, "AEP")
    assert len(appels) == 1
    service.niveau_au_point(45.0, 4.0, "SUP")     # autre ressource : autre zone d'alerte
    service.niveau_au_point(45.1, 4.0, "AEP")     # autre point
    assert len(appels) == 3


def test_client_lien_d_arrete_non_https_ignore_et_coordonnees_bornees(appels_http):
    appels, reponse = appels_http
    reponse["valeur"] = FausseReponse(200, [_zone("crise", arrete={"id": 1, "cheminFichier": "javascript:alert(1)"})])
    assert VigieauService().niveau_au_point(45.0, 4.0, "AEP").arrete_url is None
    with pytest.raises(VigieauIndisponibleError):
        VigieauService().niveau_au_point(89.0, 4.0, "AEP")
    with pytest.raises(ValueError):
        VigieauService().niveau_au_point(45.0, 4.0, "XYZ")
    assert len(appels) == 1


# --- API : refus des arrosages interdits et registre -------------------------------------------

def aujourd_hui() -> date:
    return datetime.now(settings.fuseau).date()


def hier_a(heure: int) -> str:
    """Hier à l'heure locale donnée, en UTC (ISO)."""
    local = datetime.combine(aujourd_hui() - timedelta(days=1), time(heure), tzinfo=settings.fuseau)
    return local.astimezone(UTC).isoformat()


def poser_niveau(db, espace_id: int, niveau: str, jour: date | None = None, zone: str = "Zone Saône") -> None:
    db.add(RestrictionSecheresse(espace_id=espace_id, date=jour or aujourd_hui(), niveau=niveau, zone_nom=zone,
                                 type_zone="AEP"))
    db.commit()


def arroser(client, headers, espace_id: int, **champs):
    payload = {"espace_id": espace_id, "type": "arrosage", "statut": "terminee", "volume_eau_l": 500, **champs}
    return client.post(f"{API}/interventions/", json=payload, headers=headers)


def test_arrosage_refuse_en_crise_avec_motif(client, db, vigieau):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    vigieau.niveau = CRISE                       # aucun relevé du jour : lu à la demande
    r = arroser(client, alice, espace["id"])
    assert r.status_code == 409
    assert r.json()["detail"].startswith("Arrosage interdit : niveau crise (arrêté sécheresse)")
    assert "Zone d'alerte : Zone test." in r.json()["detail"]
    assert vigieau.appels == [(45.76, 4.83, "AEP")]
    assert client.get(f"{API}/interventions/", headers=alice).json() == []
    # Planifié sans date, sous interdiction totale : refusé aussi ; une taille reste possible
    r = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "arrosage"}, headers=alice)
    assert r.status_code == 409
    r = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "taille",
                                                   "statut": "terminee"}, headers=alice)
    assert r.status_code == 201 and r.json()["secheresse_niveau"] is None


def test_arrosage_en_alerte_refuse_a_12_h_accepte_a_19_h(client, db):
    alice = creer_compte(client)
    espace = creer_espace(client, alice, ville="Lyon")
    poser_niveau(db, espace["id"], ALERTE, aujourd_hui() - timedelta(days=1))
    r = arroser(client, alice, espace["id"], realisee_le=hier_a(12))
    assert r.status_code == 409 and "interdit de 11 h à 18 h" in r.json()["detail"]
    r = arroser(client, alice, espace["id"], realisee_le=hier_a(19))
    assert r.status_code == 201, r.text
    corps = r.json()
    assert (corps["secheresse_niveau"], corps["secheresse_plage_interdite"]) == (ALERTE, "11:00–18:00")
    assert corps["secheresse_zone"] == "Zone Saône" and corps["secheresse_derogation"] is None
    assert corps["arrosage_compte_mm"] == 0.5 and corps["avertissement_secheresse"] is None


def test_derogation_jeune_plantation_enregistree(client, db):
    alice = creer_compte(client)
    espace = creer_espace(client, alice, date_plantation=(aujourd_hui() - timedelta(days=400)).isoformat())
    poser_niveau(db, espace["id"], CRISE, aujourd_hui() - timedelta(days=1))
    assert arroser(client, alice, espace["id"], realisee_le=hier_a(12)).status_code == 409
    r = arroser(client, alice, espace["id"], realisee_le=hier_a(20))
    assert r.status_code == 201, r.text
    assert r.json()["secheresse_derogation"] == "Jeune plantation de moins de 2 ans"
    assert r.json()["secheresse_niveau"] == CRISE


def test_derogation_eau_de_recuperation(client, db, vigieau):
    alice = creer_compte(client)
    espace = creer_espace(client, alice, source_eau="recuperation")
    vigieau.niveau = CRISE
    r = arroser(client, alice, espace["id"])
    assert r.status_code == 201, r.text
    assert "récupération" in r.json()["secheresse_derogation"]
    assert vigieau.appels[0][2] is None            # aucune ressource prélevée : zone la plus sévère


def test_source_d_eau_choisit_le_type_de_zone(client, vigieau):
    alice = creer_compte(client)
    forage = creer_espace(client, alice, nom="Forage", source_eau="forage", latitude=45.1)
    riviere = creer_espace(client, alice, nom="Rivière", source_eau="riviere", latitude=45.2)
    assert arroser(client, alice, forage["id"]).status_code == 201
    assert arroser(client, alice, riviere["id"]).status_code == 201
    assert [a[2] for a in vigieau.appels] == ["SOU", "SUP"]


def test_vigieau_indisponible_pas_de_blocage_mais_avertissement(client, db, vigieau):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    vigieau.disponible = False
    r = arroser(client, alice, espace["id"])
    assert r.status_code == 201, r.text
    assert r.json()["secheresse_niveau"] == INCONNU
    assert "indisponible" in r.json()["avertissement_secheresse"]


def test_terminer_un_arrosage_devenu_interdit_est_refuse(client, db):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    poser_niveau(db, espace["id"], AUCUNE)
    planifie = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "arrosage"},
                           headers=alice).json()
    db.query(RestrictionSecheresse).update({"niveau": CRISE})
    db.commit()
    r = client.put(f"{API}/interventions/{planifie['id']}", json={"statut": "terminee", "volume_eau_l": 300},
                   headers=alice)
    assert r.status_code == 409
    relu = client.get(f"{API}/interventions/{planifie['id']}", headers=alice).json()
    assert relu["statut"] == "planifiee" and relu["volume_eau_l"] is None
    # Modifier la description d'un arrosage ne le soumet pas à un nouveau contrôle
    assert client.put(f"{API}/interventions/{planifie['id']}", json={"description": "tonne"},
                      headers=alice).status_code == 200


def test_releve_du_jour_conserve_apres_un_refus(client, db, vigieau):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    vigieau.niveau = CRISE
    assert arroser(client, alice, espace["id"]).status_code == 409
    db.expire_all()
    releve = db.query(RestrictionSecheresse).filter_by(espace_id=espace["id"]).one()
    assert (releve.date, releve.niveau, releve.zone_nom) == (aujourd_hui(), CRISE, "Zone test")
    assert arroser(client, alice, espace["id"]).status_code == 409
    assert len(vigieau.appels) == 1                # relevé gardé : VigiEau n'est pas relu à chaque tentative
    assert client.get(f"{API}/interventions/", headers=alice).json() == []


def test_realisation_dans_le_futur_refusee_meme_sans_volume(client, db, vigieau):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    poser_niveau(db, espace["id"], ALERTE)
    demain_soir = datetime.combine(aujourd_hui() + timedelta(days=1), time(20), tzinfo=settings.fuseau)
    r = client.post(f"{API}/interventions/", headers=alice, json={
        "espace_id": espace["id"], "type": "arrosage", "statut": "terminee", "realisee_le": demain_soir.isoformat()})
    assert r.status_code == 422 and "futur" in r.json()["detail"]
    dans_une_heure = datetime.now(UTC) + timedelta(hours=1)
    r = client.post(f"{API}/interventions/", headers=alice, json={
        "espace_id": espace["id"], "type": "arrosage", "statut": "terminee", "realisee_le": dans_une_heure.isoformat()})
    assert r.status_code == 422
    assert client.get(f"{API}/interventions/", headers=alice).json() == []
    assert vigieau.appels == []


def test_registre_d_un_arrosage_realise_reste_fige(client, db):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    hier = aujourd_hui() - timedelta(days=1)
    poser_niveau(db, espace["id"], ALERTE, hier)
    fait = arroser(client, alice, espace["id"], realisee_le=hier_a(19))
    assert fait.status_code == 201, fait.text
    fait = fait.json()

    # Les règles et le niveau changent ensuite : le registre déjà figé n'est ni refusé ni réécrit
    db.query(RestrictionSecheresse).update({"niveau": CRISE})
    db.commit()
    r = client.put(f"{API}/interventions/{fait['id']}", headers=alice,
                   json={"planifiee_le": hier_a(8), "statut": "terminee", "volume_eau_l": 600,
                         "realisee_le": fait["realisee_le"]})
    assert r.status_code == 200, r.text
    assert (r.json()["secheresse_niveau"], r.json()["secheresse_plage_interdite"]) == (ALERTE, "11:00–18:00")

    # Déplacer l'heure de réalisation (19 h → 12 h) : refusé, le registre ne se réécrit pas
    r = client.put(f"{API}/interventions/{fait['id']}", headers=alice, json={"realisee_le": hier_a(12)})
    assert r.status_code == 409 and "figée" in r.json()["detail"]
    relu = client.get(f"{API}/interventions/{fait['id']}", headers=alice).json()
    assert relu["realisee_le"] == fait["realisee_le"]
    assert relu["secheresse_niveau"] == ALERTE and relu["volume_eau_l"] == 600


def test_registre_agent_supprime_jamais_attribue_au_createur(client, db):
    alice = creer_compte(client)
    technicien = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    espace = creer_espace(client, alice)
    poser_niveau(db, espace["id"], AUCUNE)
    planifie = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "arrosage"},
                           headers=alice).json()
    assert client.put(f"{API}/interventions/{planifie['id']}", json={"statut": "terminee", "volume_eau_l": 50},
                      headers=technicien).status_code == 200
    db.query(User).filter_by(email="tech@example.com").delete()
    db.commit()
    lignes = lire_csv(client.get(f"{API}/secheresse/registre", headers=alice))
    assert lignes[1][8] == "inconnu (compte supprimé ou non renseigné)"


def test_registre_fige_l_agent_qui_termine(client, db):
    alice = creer_compte(client)
    technicien = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    espace = creer_espace(client, alice)
    poser_niveau(db, espace["id"], VIGILANCE)
    planifie = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "arrosage"},
                           headers=alice).json()
    r = client.put(f"{API}/interventions/{planifie['id']}", json={"statut": "terminee", "volume_eau_l": 200},
                   headers=technicien)
    assert r.status_code == 200, r.text
    tech_id = client.get(f"{API}/users/me", headers=technicien).json()["id"]
    assert r.json()["realisee_par"] == tech_id and r.json()["secheresse_niveau"] == VIGILANCE
    # Repasser en planifié efface le registre
    r = client.put(f"{API}/interventions/{planifie['id']}", json={"statut": "planifiee"}, headers=alice)
    assert r.json()["realisee_par"] is None and r.json()["secheresse_niveau"] is None


def test_annuler_un_arrosage_realise_reste_possible_en_crise(client, db, meteo):
    alice = creer_compte(client)
    technicien = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    espace = creer_espace(client, alice)
    poser_niveau(db, espace["id"], AUCUNE, aujourd_hui() - timedelta(days=1))
    fait = arroser(client, technicien, espace["id"], realisee_le=hier_a(12))
    assert fait.status_code == 201, fait.text
    poser_niveau(db, espace["id"], CRISE)                     # crise aujourd'hui

    # Annuler n'est pas arroser : accepté sans contrôle, registre effacé, apport retiré du bilan
    r = client.put(f"{API}/interventions/{fait.json()['id']}", json={"statut": "planifiee"}, headers=technicien)
    assert r.status_code == 200, r.text
    corps = r.json()
    assert corps["realisee_le"] is None and corps["arrosage_compte_mm"] is None
    assert corps["secheresse_niveau"] is None and corps["realisee_par"] is None
    # Le terminer à nouveau, ou le replanifier à une nouvelle date, reste contrôlé
    r = client.put(f"{API}/interventions/{fait.json()['id']}", json={"statut": "terminee"}, headers=technicien)
    assert r.status_code == 409 and "crise" in r.json()["detail"]

    autre = arroser(client, alice, espace["id"], realisee_le=hier_a(9)).json()
    demain = datetime.combine(aujourd_hui() + timedelta(days=1), time(20), tzinfo=settings.fuseau).isoformat()
    r = client.put(f"{API}/interventions/{autre['id']}", json={"statut": "planifiee", "planifiee_le": demain},
                   headers=alice)
    assert r.status_code == 409
    r = client.put(f"{API}/interventions/{autre['id']}", json={"statut": "en_cours"}, headers=alice)
    assert r.status_code == 200 and r.json()["secheresse_niveau"] is None
    assert len(lire_csv(client.get(f"{API}/secheresse/registre", headers=alice))) == 1


def test_arrosage_antidate_sans_releve_prend_le_releve_le_plus_proche(client, db, meteo, vigieau):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    poser_niveau(db, espace["id"], CRISE)                     # crise aujourd'hui, aucun relevé hier
    r = arroser(client, alice, espace["id"], realisee_le=hier_a(20))
    assert r.status_code == 409 and "crise" in r.json()["detail"]
    assert "Niveau relevé le" in r.json()["detail"] and r.json()["detail"].count("relevé le") == 1

    # Relevés à égale distance : le plus sévère ; plus près d'un jour sans restriction : celui-là
    avant_hier = aujourd_hui() - timedelta(days=2)
    poser_niveau(db, espace["id"], AUCUNE, avant_hier)
    assert arroser(client, alice, espace["id"], realisee_le=hier_a(20)).status_code == 409
    il_y_a_3_jours = datetime.combine(aujourd_hui() - timedelta(days=3), time(20), tzinfo=settings.fuseau)
    r = arroser(client, alice, espace["id"], realisee_le=il_y_a_3_jours.isoformat())
    assert r.status_code == 201, r.text
    assert r.json()["secheresse_niveau"] == AUCUNE
    assert r.json()["secheresse_zone"] == f"Zone Saône (niveau relevé le {avant_hier.isoformat()})"

    # Aucun relevé à moins de 7 jours : niveau inconnu, non bloquant mais signalé
    il_y_a_20_jours = datetime.now(UTC) - timedelta(days=20)
    r = arroser(client, alice, espace["id"], realisee_le=il_y_a_20_jours.isoformat())
    assert r.status_code == 201 and r.json()["secheresse_niveau"] == INCONNU
    assert vigieau.appels == []                               # un jour passé n'est jamais relu


def test_arrosage_du_matin_saisi_l_apres_midi_en_alerte(client, db, meteo):
    """Arrosé à 7 h, saisi après coup : contrôlé et inscrit au registre à l'heure de l'arrosage."""
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    poser_niveau(db, espace["id"], ALERTE, aujourd_hui() - timedelta(days=1))
    r = arroser(client, alice, espace["id"], realisee_le=hier_a(7))
    assert r.status_code == 201, r.text
    assert module_secheresse.meme_instant(datetime.fromisoformat(r.json()["realisee_le"]),
                                          datetime.fromisoformat(hier_a(7)))
    # Terminer un arrosage planifié à l'heure réelle (page Rapports)
    planifie = client.post(f"{API}/interventions/", headers=alice, json={
        "espace_id": espace["id"], "type": "arrosage", "planifiee_le": hier_a(7)}).json()
    r = client.put(f"{API}/interventions/{planifie['id']}", headers=alice,
                   json={"statut": "terminee", "volume_eau_l": 200, "realisee_le": hier_a(8)})
    assert r.status_code == 200, r.text
    assert r.json()["secheresse_niveau"] == ALERTE
    lignes = lire_csv(client.get(f"{API}/secheresse/registre", headers=alice))
    heures = sorted(ligne[0][-5:] for ligne in lignes[1:])
    assert heures == ["07:00", "08:00"]


def test_releve_du_jour_manquant_et_vigieau_en_panne_reprend_la_veille(client, db, meteo, vigieau):
    """Crise relevée hier, VigiEau en panne avant le premier passage du worker : toujours interdit."""
    alice = creer_compte(client)
    espace = espace_avec_bilan(client, db, alice, 30.0)
    poser_niveau(db, espace["id"], CRISE, aujourd_hui() - timedelta(days=1))
    vigieau.disponible = False
    r = arroser(client, alice, espace["id"])
    assert r.status_code == 409 and "crise" in r.json()["detail"] and "Niveau relevé le" in r.json()["detail"]
    lu = lecture(client, alice, espace["id"])
    assert lu["secheresse"]["niveau"] == CRISE and lu["decision"]["code"] == "interdit"
    assert lu["secheresse"]["releve_du"] == (aujourd_hui() - timedelta(days=1)).isoformat()
    assert client.get(f"{API}/espaces-verts/{espace['id']}/prevision",
                      headers=alice).json()["decision"]["code"] == "interdit"
    etat = client.get(f"{API}/secheresse/etat", headers=alice).json()
    assert etat["espaces"][0]["niveau"] == CRISE and "dernier niveau connu" in etat["avertissement"]
    assert etat["synthese"]["espaces_niveau_inconnu"] == 0

    # Dernier relevé de plus de 7 jours : niveau inconnu, non bloquant mais signalé
    db.query(RestrictionSecheresse).update({"date": aujourd_hui() - timedelta(days=8)})
    db.commit()
    r = arroser(client, alice, espace["id"])
    assert r.status_code == 201 and r.json()["secheresse_niveau"] == INCONNU
    assert lecture(client, alice, espace["id"])["secheresse"]["niveau"] == INCONNU


def test_releve_en_vigueur_isole_par_espace(client, db):
    alice = creer_compte(client)
    bob = creer_compte(client, "bob@example.com")
    a = creer_espace(client, alice)
    b = creer_espace(client, bob)
    poser_niveau(db, a["id"], CRISE, aujourd_hui() - timedelta(days=2))
    poser_niveau(db, a["id"], ALERTE, aujourd_hui() - timedelta(days=1))
    poser_niveau(db, b["id"], VIGILANCE, aujourd_hui() - timedelta(days=9))
    repo = RestrictionSecheresseRepositoryImpl(db)
    retenus = module_secheresse.restrictions_en_vigueur([a["id"], b["id"]], aujourd_hui(), repo)
    assert {k: v.niveau for k, v in retenus.items()} == {a["id"]: ALERTE}     # le plus récent, à 7 jours
    assert client.get(f"{API}/secheresse/etat", headers=bob).json()["espaces"][0]["niveau"] == INCONNU


def test_actualisation_libere_la_session_et_respecte_le_budget(client, db, vigieau, monkeypatch):
    alice = creer_compte(client)
    for i in range(4):
        creer_espace(client, alice, nom=f"Espace {i}", latitude=45.0 + i / 10)
    espaces = db.query(EspaceVert).order_by(EspaceVert.id).all()
    evenements = []
    lire = vigieau.niveau_au_point

    def niveau_lent(*args):
        evenements.append("appel")
        return lire(*args)
    monkeypatch.setattr(vigieau, "niveau_au_point", niveau_lent)
    instants = iter([0, 0, 10, 70])                # début, puis avant chaque appel : budget dépassé au 3e
    monkeypatch.setattr(module_secheresse, "horloge", SimpleNamespace(monotonic=lambda: next(instants)))
    rapport = module_secheresse.actualiser_restrictions(
        espaces, RestrictionSecheresseRepositoryImpl(db), vigieau, aujourd_hui(), datetime.now(UTC),
        liberer=lambda: evenements.append("liberer"), budget_s=60)
    assert evenements == ["liberer", "appel", "appel"]
    assert (rapport.lus, rapport.echecs) == (2, 2)


def test_realisation_trop_ancienne_refusee(client, db, meteo):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    poser_niveau(db, espace["id"], CRISE)
    for realisee_le in ("2020-07-01T12:00:00Z", (datetime.now(UTC) - timedelta(days=31)).isoformat()):
        r = arroser(client, alice, espace["id"], realisee_le=realisee_le)
        assert r.status_code == 422 and "30 jours" in r.json()["detail"]
    assert client.get(f"{API}/interventions/", headers=alice).json() == []
    # Une taille ancienne n'est pas concernée
    r = client.post(f"{API}/interventions/", headers=alice, json={
        "espace_id": espace["id"], "type": "taille", "statut": "terminee", "realisee_le": "2020-07-01T12:00:00Z"})
    assert r.status_code == 201


def lire_csv(r) -> list[list[str]]:
    assert r.content.startswith("\ufeff".encode())
    return list(csv.reader(io.StringIO(r.content.decode("utf-8-sig")), delimiter=";"))


def test_registre_csv(client, db):
    alice = creer_compte(client)
    lecteur = ajouter_membre(client, db, alice, "elu@example.com", "lecteur")
    technicien = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    espace = creer_espace(client, alice, nom="Square Gare", ville="Lyon",
                          date_plantation=(aujourd_hui() - timedelta(days=100)).isoformat())
    piege = creer_espace(client, alice, nom="=HYPERLINK(\"http://x\")", ville="Lyon", latitude=45.0)
    hier = aujourd_hui() - timedelta(days=1)
    poser_niveau(db, espace["id"], CRISE, hier)
    poser_niveau(db, piege["id"], ALERTE, hier)
    assert arroser(client, alice, espace["id"], realisee_le=hier_a(20), volume_eau_l=1250.5).status_code == 201
    assert arroser(client, alice, piege["id"], realisee_le=hier_a(7)).status_code == 201

    r = client.get(f"{API}/secheresse/registre", params={"du": hier.isoformat(), "au": aujourd_hui().isoformat()},
                   headers=lecteur)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")
    assert "registre_secheresse_" in r.headers["content-disposition"]
    lignes = lire_csv(r)
    assert lignes[0] == ["Date/heure", "Espace", "Commune", "Volume (L)", "Niveau VigiEau", "Plage autorisée",
                         "Dérogation", "Zone d'alerte", "Agent"]
    assert len(lignes) == 3
    piege_lu, square = lignes[1], lignes[2]                      # par date de réalisation
    assert piege_lu[0] == f"{hier.isoformat()} 07:00"
    assert piege_lu[1].startswith("'=")                           # pas de formule exécutée par le tableur
    assert piege_lu[4:6] == ["alerte", "hors 11:00–18:00"]
    assert square == [f"{hier.isoformat()} 20:00", "Square Gare", "Lyon", "1250,5", "crise", "hors 11:00–18:00",
                      "Jeune plantation de moins de 2 ans", "Zone Saône", "Alice"]

    # Hors période : vide ; période incohérente ou trop longue : refusée ; technicien : refusé
    vide = client.get(f"{API}/secheresse/registre", params={"du": "2020-01-01", "au": "2020-01-31"}, headers=alice)
    assert len(lire_csv(vide)) == 1
    assert client.get(f"{API}/secheresse/registre", params={"du": "2026-02-01", "au": "2026-01-01"},
                      headers=alice).status_code == 422
    assert client.get(f"{API}/secheresse/registre", params={"du": "2020-01-01", "au": "2026-01-01"},
                      headers=alice).status_code == 422
    # Dates hors bornes : 422, jamais une erreur interne (débordement des conversions de fuseau)
    for bornes in ({"du": "9999-12-29", "au": "9999-12-31"}, {"du": "0001-01-01", "au": "0001-01-02"}):
        assert client.get(f"{API}/secheresse/registre", params=bornes, headers=alice).status_code == 422
    assert client.get(f"{API}/secheresse/registre", headers=technicien).status_code == 403
    client.cookies.clear()
    assert client.get(f"{API}/secheresse/registre").status_code == 401


def test_registre_arrosage_anterieur_au_registre(client, db):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    db.add(Intervention(espace_id=espace["id"], type="arrosage", statut="terminee", volume_eau_l=10,
                        realisee_le=datetime.now(UTC) - timedelta(hours=1)))
    db.commit()
    lignes = lire_csv(client.get(f"{API}/secheresse/registre", headers=alice))
    assert lignes[1][4:6] == ["non enregistré (antérieur au registre)", ""]


def test_registre_et_etat_isoles_entre_organisations(client, db, vigieau):
    alice = creer_compte(client)
    bob = creer_compte(client, "bob@example.com")
    espace_alice = creer_espace(client, alice, nom="Parc d'Alice")
    creer_espace(client, bob, nom="Parc de Bob", latitude=44.0)
    vigieau.par_point[(45.76, 4.83)] = CRISE
    assert arroser(client, alice, espace_alice["id"]).status_code == 409
    poser_niveau(db, espace_alice["id"], AUCUNE, aujourd_hui() - timedelta(days=1))
    assert arroser(client, alice, espace_alice["id"], realisee_le=hier_a(10)).status_code == 201

    assert len(lire_csv(client.get(f"{API}/secheresse/registre", headers=bob))) == 1
    assert len(lire_csv(client.get(f"{API}/secheresse/registre", headers=alice))) == 2
    etat_bob = client.get(f"{API}/secheresse/etat", headers=bob).json()
    assert [e["nom"] for e in etat_bob["espaces"]] == ["Parc de Bob"]
    assert etat_bob["espaces"][0]["niveau"] == INCONNU        # Bob n'a pas encore de relevé du jour


def test_etat_secheresse_et_actualisation(client, db, vigieau):
    alice = creer_compte(client)
    technicien = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    creer_espace(client, alice, nom="Gazon", type_espace="Square", latitude=45.1)
    creer_espace(client, alice, nom="Alignement", type_espace="Rue", latitude=45.2)
    creer_espace(client, alice, nom="Jeunes tilleuls", type_espace="Parc", latitude=45.3,
                 date_plantation=(aujourd_hui() - timedelta(days=30)).isoformat())
    avant = client.get(f"{API}/secheresse/etat", headers=alice).json()
    assert avant["synthese"]["espaces_niveau_inconnu"] == 3 and "inconnu" in avant["avertissement"]

    assert client.post(f"{API}/secheresse/actualiser", headers=technicien).status_code == 403
    vigieau.par_point = {(45.1, 4.83): CRISE, (45.2, 4.83): ALERTE, (45.3, 4.83): CRISE}
    r = client.post(f"{API}/secheresse/actualiser", headers=alice)
    assert r.status_code == 200, r.text
    etat = r.json()
    assert [e["nom"] for e in etat["espaces"]] == ["Jeunes tilleuls", "Alignement", "Gazon"]   # priorités
    jeunes, alignement, gazon = etat["espaces"]
    assert jeunes["priorite_libelle"] == "Jeunes plantations" and jeunes["derogation"] is not None
    assert alignement["plage_interdite"] == "11:00–18:00" and alignement["interdit_toute_la_journee"] is False
    assert gazon["interdit_toute_la_journee"] is True and gazon["zone_nom"] == "Zone test"
    assert gazon["arrete_url"] == "https://example.org/arrete.pdf"
    synthese = etat["synthese"]
    assert synthese["niveau_max"] == CRISE and synthese["par_niveau"]["crise"] == 2
    assert synthese["espaces_interdits"] == 1 and synthese["espaces_avec_plage"] == 2
    assert synthese["espaces_niveau_inconnu"] == 0 and etat["avertissement"] is None
    assert synthese["derniere_actualisation"] is not None and "VigiEau" in etat["source"]
    assert client.get(f"{API}/secheresse/etat", headers=technicien).json()["synthese"] == synthese
    client.cookies.clear()
    assert client.get(f"{API}/secheresse/etat").status_code == 401


def test_actualisation_cesse_apres_des_erreurs_successives_et_limitee(client, vigieau):
    alice = creer_compte(client)
    for i in range(5):
        creer_espace(client, alice, nom=f"Espace {i}", latitude=45.0 + i / 10)
    vigieau.disponible = False                     # erreur HTTP (pas une panne réseau) à chaque point
    r = client.post(f"{API}/secheresse/actualiser", headers=alice)
    assert r.status_code == 200 and r.json()["synthese"]["espaces_niveau_inconnu"] == 5
    assert len(vigieau.appels) == 3                # trois échecs de suite : les suivants ne sont pas interrogés
    for _ in range(4):
        assert client.post(f"{API}/secheresse/actualiser", headers=alice).status_code == 200
    r = client.post(f"{API}/secheresse/actualiser", headers=alice)
    assert r.status_code == 429 and "Retry-After" in r.headers
    # Le compteur est propre à l'organisation
    bob = creer_compte(client, "bob@example.com")
    assert client.post(f"{API}/secheresse/actualiser", headers=bob).status_code == 200


def test_releve_concurrent_du_meme_jour_sans_erreur_d_unicite(client, db, monkeypatch):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    poser_niveau(db, espace["id"], ALERTE)          # écrit entre-temps par le worker
    repo = RestrictionSecheresseRepositoryImpl(db)
    monkeypatch.setattr(repo, "get", lambda *_: None)   # la requête ne l'a pas encore vu
    releve = repo.enregistrer(espace["id"], aujourd_hui(), NiveauVigieau(niveau=CRISE, zone_nom="Zone B"),
                              datetime.now(UTC))
    db.commit()
    assert (releve.niveau, releve.zone_nom) == (CRISE, "Zone B")
    assert db.query(RestrictionSecheresse).filter_by(espace_id=espace["id"]).count() == 1


def test_actualisation_sans_aucun_niveau_lu_journalisee_en_erreur(client, vigieau, monkeypatch):
    erreurs = []
    monkeypatch.setattr(module_secheresse.logger, "error", lambda message, *args: erreurs.append(message % args))
    alice = creer_compte(client)
    creer_espace(client, alice)
    vigieau.disponible = False
    assert client.post(f"{API}/secheresse/actualiser", headers=alice).status_code == 200
    assert len(erreurs) == 1 and "Aucun niveau VigiEau relevé" in erreurs[0]
    vigieau.disponible = True
    assert client.post(f"{API}/secheresse/actualiser", headers=alice).status_code == 200
    assert len(erreurs) == 1


def test_actualisation_vigieau_injoignable_sans_erreur(client, vigieau):
    alice = creer_compte(client)
    creer_espace(client, alice, latitude=45.1)
    creer_espace(client, alice, latitude=45.2)
    vigieau.injoignable = True
    r = client.post(f"{API}/secheresse/actualiser", headers=alice)
    assert r.status_code == 200 and r.json()["synthese"]["espaces_niveau_inconnu"] == 2
    assert len(vigieau.appels) == 1                # panne générale : pas un délai d'attente par espace


# --- Paramètres de l'organisation --------------------------------------------------------------

REGLES_PERSONNALISEES = {
    "niveaux": {
        "vigilance": {"interdit": False, "plage_interdite": None},
        "alerte": {"interdit": False, "plage_interdite": {"debut": "08:00", "fin": "20:00"}},
        "alerte_renforcee": {"interdit": True, "plage_interdite": None},
        "crise": {"interdit": True, "plage_interdite": None},
    },
    "derogations": {"jeunes_plantations_ans": 3, "plage_interdite_jeunes_plantations": None,
                    "eau_recuperation": True},
}


def test_regles_de_l_organisation_lecture_et_ecriture_admin(client, db):
    alice = creer_compte(client)
    gestionnaire = ajouter_membre(client, db, alice, "gest@example.com", "gestionnaire")
    technicien = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    defaut = client.get(f"{API}/organisations/moi/secheresse", headers=technicien).json()
    assert defaut["personnalisees"] is False and "guide national" in defaut["source"]
    assert defaut["niveaux"]["alerte"]["plage_interdite"] == {"debut": "11:00", "fin": "18:00"}
    assert defaut["derogations"]["jeunes_plantations_ans"] == 2

    assert client.put(f"{API}/organisations/moi/secheresse", json=REGLES_PERSONNALISEES,
                      headers=gestionnaire).status_code == 403
    r = client.put(f"{API}/organisations/moi/secheresse", json=REGLES_PERSONNALISEES, headers=alice)
    assert r.status_code == 200, r.text
    assert r.json()["personnalisees"] is True and r.json()["derogations"]["jeunes_plantations_ans"] == 3

    # Les règles s'appliquent aux arrosages : 19 h tombe désormais dans la plage interdite de l'alerte
    espace = creer_espace(client, alice)
    poser_niveau(db, espace["id"], ALERTE, aujourd_hui() - timedelta(days=1))
    assert arroser(client, alice, espace["id"], realisee_le=hier_a(19)).status_code == 409
    assert arroser(client, alice, espace["id"], realisee_le=hier_a(21)).status_code == 201

    # Les paramètres généraux (gestionnaire) ne touchent pas aux règles sécheresse
    r = client.put(f"{API}/organisations/moi", headers=gestionnaire,
                   json={"parametres": {"prix_m3": 4.2, "secheresse": {"niveaux": {}}}})
    assert r.status_code == 200
    assert r.json()["parametres"]["prix_m3"] == 4.2
    assert r.json()["parametres"]["secheresse"]["derogations"]["jeunes_plantations_ans"] == 3


@pytest.mark.parametrize("modification", [
    {"alerte": {"interdit": False, "plage_interdite": {"debut": "18:00", "fin": "11:00"}}},
    {"alerte": {"interdit": False, "plage_interdite": {"debut": "25:00", "fin": "26:00"}}},
    {"alerte": {"interdit": False, "plage_interdite": {"debut": "11h", "fin": "18h"}}},
])
def test_regles_invalides_refusees(client, modification):
    alice = creer_compte(client)
    regles = {**REGLES_PERSONNALISEES, "niveaux": {**REGLES_PERSONNALISEES["niveaux"], **modification}}
    assert client.put(f"{API}/organisations/moi/secheresse", json=regles, headers=alice).status_code == 422
    trop_vieux = {**REGLES_PERSONNALISEES, "derogations": {"jeunes_plantations_ans": 50}}
    assert client.put(f"{API}/organisations/moi/secheresse", json=trop_vieux, headers=alice).status_code == 422


def test_regle_omise_prend_le_defaut_ou_est_exigee(client, db):
    alice = creer_compte(client)
    # Niveau incomplet : refusé (il lèverait l'interdiction de crise sans le dire)
    incomplet = {**REGLES_PERSONNALISEES, "niveaux": {**REGLES_PERSONNALISEES["niveaux"], "crise": {}}}
    assert client.put(f"{API}/organisations/moi/secheresse", json=incomplet, headers=alice).status_code == 422
    sans_plage = {**REGLES_PERSONNALISEES, "niveaux": {**REGLES_PERSONNALISEES["niveaux"],
                                                       "crise": {"interdit": False}}}
    assert client.put(f"{API}/organisations/moi/secheresse", json=sans_plage, headers=alice).status_code == 422
    # Dérogation sans plage : la plage du guide (11 h–18 h) s'applique, pas « aucune plage »
    r = client.put(f"{API}/organisations/moi/secheresse", headers=alice,
                   json={"niveaux": REGLES_PERSONNALISEES["niveaux"], "derogations": {"jeunes_plantations_ans": 2}})
    assert r.status_code == 200, r.text
    assert r.json()["derogations"]["plage_interdite_jeunes_plantations"] == {"debut": "11:00", "fin": "18:00"}
    espace = creer_espace(client, alice, date_plantation=(aujourd_hui() - timedelta(days=100)).isoformat())
    poser_niveau(db, espace["id"], CRISE, aujourd_hui() - timedelta(days=1))
    assert arroser(client, alice, espace["id"], realisee_le=hier_a(12)).status_code == 409
    assert arroser(client, alice, espace["id"], realisee_le=hier_a(20)).status_code == 201
    # Champ inconnu (faute de frappe) : refusé plutôt qu'ignoré
    faute = {**REGLES_PERSONNALISEES, "derogations": {"jeunes_plantation_ans": 1}}
    assert client.put(f"{API}/organisations/moi/secheresse", json=faute, headers=alice).status_code == 422


def test_regles_isolees_entre_organisations(client, db):
    alice = creer_compte(client)
    bob = creer_compte(client, "bob@example.com")
    client.put(f"{API}/organisations/moi/secheresse", json=REGLES_PERSONNALISEES, headers=alice)
    assert client.get(f"{API}/organisations/moi/secheresse", headers=bob).json()["personnalisees"] is False


# --- Espaces ------------------------------------------------------------------------------------

def test_espace_source_d_eau_et_date_de_plantation(client):
    alice = creer_compte(client)
    espace = creer_espace(client, alice)
    assert espace["source_eau"] == "reseau" and espace["date_plantation"] is None
    r = client.put(f"{API}/espaces-verts/{espace['id']}", headers=alice,
                   json={"source_eau": "forage", "date_plantation": "2026-03-01"})
    assert (r.json()["source_eau"], r.json()["date_plantation"]) == ("forage", "2026-03-01")
    assert client.put(f"{API}/espaces-verts/{espace['id']}", json={"source_eau": None},
                      headers=alice).status_code == 422
    assert client.post(f"{API}/espaces-verts/", headers=alice, json={
        "nom": "X", "latitude": 45, "longitude": 4, "source_eau": "citerne"}).status_code == 422
    # Date de plantation future (2062 pour 2026) : refusée plutôt que de priver l'espace de sa dérogation
    futur = (aujourd_hui() + timedelta(days=30)).isoformat()
    assert client.put(f"{API}/espaces-verts/{espace['id']}", json={"date_plantation": futur},
                      headers=alice).status_code == 422
    assert client.post(f"{API}/espaces-verts/", headers=alice, json={
        "nom": "X", "latitude": 45, "longitude": 4, "date_plantation": futur}).status_code == 422
    assert client.put(f"{API}/espaces-verts/{espace['id']}", json={"date_plantation": aujourd_hui().isoformat()},
                      headers=alice).status_code == 200


# --- Prévision, tableau de bord et worker -------------------------------------------------------

TAW, RAW = 46.5, 23.25


def espace_avec_bilan(client, db, headers, epuisement: float, **champs) -> dict:
    """Square sur limon (TAW 46,5 mm) avec un bilan FAO-56 du jour : arroser au plus tard demain."""
    espace = creer_espace(client, headers, type_espace="Square", type_sol="Limoneux", surface_m2=100, **champs)
    db.add(BilanHydriqueJournalier(
        espace_id=espace["id"], date=aujourd_hui(), reserve_utile_fin_journee=TAW - epuisement,
        indice_stress=epuisement / TAW, statut_hydrique="A surveiller", epuisement_debut_mm=epuisement - 3,
        epuisement_fin_mm=epuisement, et0_mm=5, kl=0.8, ks=1, etc_mm=3, pluie_mm=0, pluie_efficace_mm=0,
        arrosage_mm=0, drainage_mm=0, taw_mm=TAW, raw_mm=RAW, version_modele=VERSION_MODELE,
    ))
    db.commit()
    return espace


def lecture(client, headers, espace_id: int) -> dict:
    capteurs = client.get(f"{API}/capteurs/dashboard", headers=headers).json()["capteurs"]
    return next(c for c in capteurs if c["espace_id"] == espace_id)


def test_tableau_de_bord_tient_compte_de_la_restriction(client, db):
    alice = creer_compte(client)
    crise = espace_avec_bilan(client, db, alice, 30.0)
    alerte = espace_avec_bilan(client, db, alice, 30.0, nom="Square alerte", latitude=45.0)
    libre = espace_avec_bilan(client, db, alice, 30.0, nom="Square libre", latitude=44.0)
    poser_niveau(db, crise["id"], CRISE)
    poser_niveau(db, alerte["id"], ALERTE)

    lu = lecture(client, alice, crise["id"])
    assert lu["secheresse"]["niveau"] == CRISE and lu["secheresse"]["interdit_toute_la_journee"] is True
    assert lu["decision"]["code"] == "interdit" and lu["decision"]["dose_recommandee"] is None
    assert lu["dose_recommandee"] is None
    lu = lecture(client, alice, alerte["id"])
    assert lu["decision"]["code"] == "arroser" and lu["decision"]["plage_interdite"] == "11:00–18:00"
    assert "Arroser hors 11 h–18 h (alerte)." in lu["decision"]["texte"]
    assert lu["dose_recommandee"] is not None and lu["secheresse"]["priorite_secheresse"] == PRIORITE_AUTRES
    lu = lecture(client, alice, libre["id"])
    assert lu["secheresse"]["niveau"] == INCONNU and lu["decision"]["code"] == "arroser"
    assert "Niveau VigiEau inconnu" in lu["decision"]["texte"]

    prevision = client.get(f"{API}/espaces-verts/{crise['id']}/prevision", headers=alice).json()
    assert prevision["decision"]["code"] == "interdit"
    diagnostic = client.post(f"{API}/health/diagnostic", json={"espace_id": crise["id"]}, headers=alice).json()
    assert diagnostic["conseil_arrosage"] is None and diagnostic["dose_recommandee"] is None
    assert "interdit" in diagnostic["message"]


def test_contrat_decision_interdite_visible_dans_openapi(client):
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    assert "interdit" in schemas["DecisionDTO"]["properties"]["code"]["enum"]
    assert "secheresse" in schemas["LectureCapteurDTO"]["properties"]


def test_worker_releve_le_niveau_une_fois_par_jour_et_ne_conseille_pas_l_interdit(client, db, meteo, vigieau):
    alice = creer_compte(client)
    espace = creer_espace(client, alice, reserve_utile_max=10, coefficient_cultural=1.0)
    meteo.et0 = 9.0                                    # réserve épuisée : critique dès le premier bilan
    vigieau.niveau = CRISE
    executer_mise_a_jour(db, meteo_service=meteo)
    executer_mise_a_jour(db, meteo_service=meteo)
    assert len(vigieau.appels) == 1                    # passage horaire suivant : relevé du jour déjà fait
    db.expire_all()
    restriction = db.query(RestrictionSecheresse).filter_by(espace_id=espace["id"]).one()
    assert (restriction.date, restriction.niveau) == (aujourd_hui(), CRISE)
    notes = db.query(Notification).filter_by(type="stress_hydrique").all()
    assert len(notes) == 1 and "arrosage interdit (crise, arrêté sécheresse)" in notes[0].message
    assert db.query(Notification).filter_by(type="arrosage_a_prevoir").count() == 0


def test_worker_vigieau_en_panne_n_empeche_pas_les_bilans(client, db, meteo, vigieau):
    alice = creer_compte(client)
    creer_espace(client, alice)
    vigieau.injoignable = True
    executer_mise_a_jour(db, meteo_service=meteo)
    db.expire_all()
    assert db.query(BilanHydriqueJournalier).count() == 1
    assert db.query(RestrictionSecheresse).count() == 0
    vigieau.injoignable = False                        # passage suivant : relevé retenté
    executer_mise_a_jour(db, meteo_service=meteo)
    assert db.query(RestrictionSecheresse).count() == 1


# --- Migration ----------------------------------------------------------------------------------

def test_migration_mode_secheresse_conserve_les_donnees(monkeypatch):
    url = f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'secheresse.db')}"
    config = config_alembic(monkeypatch, url)
    command.upgrade(config, "0005_prevision_notifications")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO organisations (id, nom, slug) VALUES (1, 'Ville', 'ville')"))
        conn.execute(text("INSERT INTO users (id, name, email, hashed_password, organisation_id, role) "
                          "VALUES (1, 'Agent', 'a@example.com', 'h', 1, 'technicien')"))
        conn.execute(text("INSERT INTO espaces_verts (id, nom, latitude, longitude, organisation_id) "
                          "VALUES (10, 'Parc', 45.7, 4.8, 1)"))
        conn.execute(text(
            "INSERT INTO interventions (id, espace_id, type, statut, volume_eau_l, cree_par) VALUES "
            "(1, 10, 'arrosage', 'terminee', 100, 1), (2, 10, 'arrosage', 'planifiee', NULL, 1)"))

    command.upgrade(config, "head")
    with engine.begin() as conn:
        assert conn.execute(text("SELECT source_eau, date_plantation FROM espaces_verts")).one() == ("reseau", None)
        lignes = conn.execute(text("SELECT id, realisee_par, secheresse_niveau FROM interventions ORDER BY id")).all()
        assert [tuple(l) for l in lignes] == [(1, None, None), (2, None, None)]
        conn.execute(text("INSERT INTO restrictions_secheresse (espace_id, date, niveau) "
                          "VALUES (10, '2026-07-01', 'crise')"))
        with pytest.raises(IntegrityError), conn.begin_nested():   # un relevé par espace et par jour
            conn.execute(text("INSERT INTO restrictions_secheresse (espace_id, date, niveau) "
                              "VALUES (10, '2026-07-01', 'alerte')"))
        with pytest.raises(IntegrityError), conn.begin_nested():   # niveau contrôlé
            conn.execute(text("INSERT INTO restrictions_secheresse (espace_id, date, niveau) "
                              "VALUES (10, '2026-07-02', 'rouge')"))
        with pytest.raises(IntegrityError), conn.begin_nested():   # source d'eau contrôlée
            conn.execute(text("UPDATE espaces_verts SET source_eau = 'citerne'"))

    command.downgrade(config, "0005_prevision_notifications")
    with engine.begin() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM interventions")).scalar() == 2
        assert conn.execute(text("SELECT COUNT(*) FROM espaces_verts")).scalar() == 1
    engine.dispose()
