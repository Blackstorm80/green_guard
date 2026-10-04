"""Logique métier pure : aucun accès base de données ni réseau."""
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from application.dto.capteurs import MetriquesDashboardDTO
from application.dto.intervention import PrioriteIntervention
from application.use_cases.capteurs import _qualite_air, _synthese
from application.use_cases.interventions import lister_interventions_urgentes
from domain.logic.arrosage import calculer_besoin_arrosage_mm, calculer_volume_arrosage, convertir_besoin_en_litres
from domain.logic.bilan_carbone import CO2_KG_M2_AN, estimer_co2_absorbe_jour, estimer_o2_produit_jour
from domain.logic.bilan_hydrique import calculer_bilan_hydrique_pour_jour
from domain.logic.clustering import calculer_couleur_gauge, distance_km, nommer_zones, regrouper
from domain.logic.stress_hydrique import calculer_bilan_hydrique_simplifie, classe_sol
from domain.logic.stress_sanitaire import calculer_stress_sanitaire_jour
from domain.ports.capteurs import STATUT_SANS_DONNEE, ICapteurService, LectureCapteur


def espace(**champs):
    defaut = dict(id=1, nom="Parc", reserve_utile_max=100.0, coefficient_cultural=1.0, type_sol=None,
                  type_espace="Parc", surface_m2=1000.0, latitude=45.76, longitude=4.83)
    return SimpleNamespace(**{**defaut, **champs})


# --- Stress hydrique ---------------------------------------------------------

@pytest.mark.parametrize("reserve, statut", [(100, "Optimal"), (71, "Optimal"), (60, "A surveiller"),
                                             (41, "A surveiller"), (40, "Critique"), (0, "Critique")])
def test_seuils_de_statut(reserve, statut):
    _, _, resultat = calculer_bilan_hydrique_simplifie(reserve, 0, 0, 100, 1.0)
    assert resultat == statut


def test_reserve_bornee_entre_zero_et_maximum():
    assert calculer_bilan_hydrique_simplifie(90, 50, 0, 100, 1.0)[0] == 100   # pas de débordement
    assert calculer_bilan_hydrique_simplifie(5, 0, 50, 100, 1.0)[0] == 0      # pas de réserve négative


def test_reserve_utile_nulle_ne_divise_pas_par_zero():
    _, indice, statut = calculer_bilan_hydrique_simplifie(0, 0, 0, 0, 1.0)
    assert indice == 1.0 and statut == "Critique"


@pytest.mark.parametrize("type_sol, classe", [("Argileux", "riche"), ("sableux", "pauvre"), ("Limoneux", "moyen"),
                                              ("Limon-Argileux", "moyen"), (None, "moyen"), ("inconnu", "moyen")])
def test_classe_de_sol(type_sol, classe):
    assert classe_sol(type_sol) == classe


def test_sol_drainant_consomme_plus_vite():
    argile = calculer_bilan_hydrique_simplifie(100, 0, 10, 100, 1.0, type_sol="Argileux")[0]
    sable = calculer_bilan_hydrique_simplifie(100, 0, 10, 100, 1.0, type_sol="Sableux")[0]
    assert argile == 92 and sable == 88


# --- Bilan journalier --------------------------------------------------------

def test_premier_bilan_part_d_une_reserve_pleine():
    bilan = calculer_bilan_hydrique_pour_jour(espace(), None, pluie_jour_mm=0, et0_jour_mm=5,
                                              arrosage_jour_mm=0, date_du_jour=date(2026, 7, 1),
                                              stress_sanitaire_jour=None)
    assert bilan.reserve_utile_fin_journee == 95 and bilan.statut_hydrique == "Optimal"


def test_bilan_part_de_la_veille_et_compte_pluie_et_arrosage():
    veille = SimpleNamespace(reserve_utile_fin_journee=30.0)
    bilan = calculer_bilan_hydrique_pour_jour(espace(), veille, pluie_jour_mm=10, et0_jour_mm=5,
                                              arrosage_jour_mm=15, date_du_jour=date(2026, 7, 2),
                                              stress_sanitaire_jour=None)
    assert bilan.reserve_utile_fin_journee == 50


# --- Stress sanitaire --------------------------------------------------------

def test_stress_sanitaire():
    assert calculer_stress_sanitaire_jour([20] * 24, [55] * 24) == 0.0     # zone de confort
    assert calculer_stress_sanitaire_jour([40] * 24, [95] * 24) == 1.0     # extrêmes
    assert 0 < calculer_stress_sanitaire_jour([30] * 24, [55] * 24) < 1
    assert calculer_stress_sanitaire_jour([], []) == 0.0


# --- Arrosage ----------------------------------------------------------------

def test_arrosage():
    assert calculer_besoin_arrosage_mm(espace(), SimpleNamespace(reserve_utile_fin_journee=60)) == 0.0
    assert calculer_besoin_arrosage_mm(espace(), SimpleNamespace(reserve_utile_fin_journee=30)) == 70.0
    assert convertir_besoin_en_litres(10, 100, efficacite_systeme=0.5) == 2000
    assert convertir_besoin_en_litres(0, 100) == 0.0
    assert calculer_volume_arrosage(espace(surface_m2=10), SimpleNamespace(reserve_utile_fin_journee=40),
                                    efficacite_systeme=1.0) == 600


# --- Carbone -----------------------------------------------------------------

def test_carbone():
    jour_100_m2 = 100 * 0.306 * 44 / 12 / 365                 # Nowak & Crane (2002), converti en CO2
    assert estimer_co2_absorbe_jour(espace(surface_m2=100), 0.0, None) == pytest.approx(jour_100_m2)
    assert estimer_co2_absorbe_jour(espace(surface_m2=100), 0.5, 0.5) == pytest.approx(jour_100_m2 / 4)
    assert estimer_co2_absorbe_jour(espace(surface_m2=None), 0.0, None) == 0.0
    assert estimer_co2_absorbe_jour(espace(surface_m2=100), 1.0, None) == 0.0
    assert estimer_o2_produit_jour(espace(surface_m2=100), 0.0, None) == pytest.approx(jour_100_m2 * 32 / 44)


def test_carbone_ordre_de_grandeur_annuel():
    """Non-régression : l'ancien facteur donnait ≈ 18 kg CO2/m²/an, 15 à 20 fois trop."""
    annuel_m2 = estimer_co2_absorbe_jour(espace(surface_m2=1), 0.0, None) * 365
    assert annuel_m2 == pytest.approx(CO2_KG_M2_AN)
    assert 1.1 < annuel_m2 < 1.13


# --- Clustering --------------------------------------------------------------

def test_distance_lyon_paris():
    assert distance_km(45.764, 4.8357, 48.8566, 2.3522) == pytest.approx(392, abs=5)


def test_regroupement_geographique():
    points = [(45.76, 4.83), (45.761, 4.832), (48.85, 2.35), (48.852, 2.351)]
    groupes = regrouper(points, 2)
    assert sorted(sorted(g.indices) for g in groupes) == [[0, 1], [2, 3]]
    for g in groupes:
        assert g.rayon_km < 1                                   # deux parcs voisins
        assert 45 < g.centroid_lat < 49                         # coordonnées réelles


def test_regroupement_cas_limites():
    assert regrouper([], 3) == []
    assert len(regrouper([(45.0, 4.0)], 5)) == 1                # jamais plus de groupes que de points
    assert nommer_zones(2, "quartier") == ["Quartier 1", "Quartier 2"]


def test_couleur_de_jauge():
    assert calculer_couleur_gauge(None) == "#64748B"
    assert calculer_couleur_gauge(90) == "#0CB95D"
    assert calculer_couleur_gauge(70) == "#E77C02"
    assert calculer_couleur_gauge(10) == "#DF1B1B"


# --- Interventions urgentes --------------------------------------------------

class CapteursFictifs(ICapteurService):
    def __init__(self, lectures):
        self.lectures = lectures

    def lecture_actuelle(self, espace_):
        return self.lectures[espace_.id]

    def lectures_actuelles(self, espaces):
        return [self.lectures[e.id] for e in espaces]


def lecture(espace_id, statut="Optimal", temperature=20.0, co2=400.0):
    return LectureCapteur(espace_id=espace_id, nom=f"E{espace_id}", temperature_c=temperature,
                          humidite_percent=50, humidite_air_percent=50, co2_ppm=co2, reserve_eau_mm=10,
                          sante_percent=50, statut=statut, timestamp=datetime(2026, 7, 1, tzinfo=UTC))


def test_urgences_triees_par_vraie_priorite():
    espaces = [espace(id=1, nom="Chaud"), espace(id=2, nom="Sec")]
    capteurs = CapteursFictifs({1: lecture(1, temperature=35), 2: lecture(2, statut="Critique")})
    resultat = lister_interventions_urgentes(espaces, capteurs)
    assert [i.priorite for i in resultat.interventions] == [PrioriteIntervention.CRITICAL, PrioriteIntervention.HIGH]


def test_urgences_identifiants_stables_et_limite():
    espaces = [espace(id=i) for i in range(1, 5)]
    capteurs = CapteursFictifs({i: lecture(i, statut="Critique", co2=1500) for i in range(1, 5)})
    r1 = lister_interventions_urgentes(espaces, capteurs, limit=3)
    r2 = lister_interventions_urgentes(espaces, capteurs, limit=3)
    assert r1.total == 8 and len(r1.interventions) == 3
    assert [i.id for i in r1.interventions] == [i.id for i in r2.interventions]


def test_aucune_urgence_sans_donnee():
    capteurs = CapteursFictifs({1: lecture(1, statut=STATUT_SANS_DONNEE, temperature=None, co2=None)})
    assert lister_interventions_urgentes([espace()], capteurs).total == 0


# --- Synthèse du tableau de bord ---------------------------------------------

def metriques(**champs):
    defaut = dict(espaces_suivis=3, espaces_avec_donnees=3, espaces_stress=0, espaces_critiques=0, qualite_air="Bonne")
    return MetriquesDashboardDTO(**{**defaut, **champs})


def test_synthese_du_tableau_de_bord():
    assert _synthese(metriques(espaces_suivis=0, espaces_avec_donnees=0))[0] == "En attente"
    assert _synthese(metriques(espaces_avec_donnees=0))[0] == "En attente"
    assert _synthese(metriques(espaces_stress=2, espaces_critiques=1))[0] == "Critique"
    assert _synthese(metriques(espaces_stress=1))[0] == "Attention"
    assert _synthese(metriques())[0] == "Sain"


def test_qualite_air():
    assert [_qualite_air(v) for v in (None, 500, 900, 1500)] == ["Inconnue", "Bonne", "Moyenne", "Mauvaise"]
