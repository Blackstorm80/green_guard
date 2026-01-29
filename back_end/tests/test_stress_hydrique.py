# Fichier : tests/domain/logic/test_stress_hydrique.py

import datetime
import sys
import os

# Ajoute le répertoire racine du projet au path pour permettre les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from domain.logic.stress_hydrique import calculer_bilan_hydrique_simplifie
from tests.mocks.mock_meteo_service import FakeMeteoService


def test_calcul_bilan_hydrique_cas_optimal():
    """
    Teste le calcul du bilan hydrique dans un cas où le statut final est "Optimal".
    """
    # 1. ARRANGE: Mettre en place le scénario de test
    # Météo contrôlée : Pas de pluie, évaporation modérée
    fake_meteo_service = FakeMeteoService(pluie_mm=0.0, et0_mm=3.0)

    # Données de l'espace vert et de la veille
    reserve_eau_veille = 25.0  # mm
    arrosage_jour = 5.0  # mm (on a arrosé)
    reserve_utile_max = 30.0  # mm
    coefficient_cultural = 0.8

    # 2. ACT: Exécuter la logique à tester
    donnees_meteo = fake_meteo_service.get_donnees_meteo_jour(
        latitude=48.85, longitude=2.35, date=datetime.date.today()
    )
    total_apport_eau = arrosage_jour + donnees_meteo.pluie_mm

    nouvelle_reserve, indice_stress, statut = calculer_bilan_hydrique_simplifie(
        reserve_eau_veille=reserve_eau_veille,
        pluie_et_arrosage_jour=total_apport_eau,
        evapotranspiration_reference_jour=donnees_meteo.et0_mm,
        reserve_utile_max=reserve_utile_max,
        coefficient_cultural=coefficient_cultural,
    )

    # 3. ASSERT: Vérifier que les résultats sont corrects
    # ETc = 0.8 * 3.0 = 2.4 mm
    # Nouvelle réserve brute = 25.0 + 5.0 - 2.4 = 27.6 mm
    # Nouvelle réserve (bornée) = min(30.0, max(0, 27.6)) = 27.6 mm
    # Indice stress = 1 - (27.6 / 30.0) = 1 - 0.92 = 0.08
    # Statut = "Optimal" car 0.08 < 0.3
    assert round(nouvelle_reserve, 2) == 27.60
    assert round(indice_stress, 2) == 0.08
    assert statut == "Optimal"

def test_calcul_bilan_hydrique_cas_critique():
    """
    Teste le calcul du bilan hydrique dans un cas où le statut final est "Critique".
    """
    # ARRANGE: Journée chaude et sèche, pas d'arrosage
    fake_meteo_service = FakeMeteoService(pluie_mm=0.5, et0_mm=6.0)
    # ACT
    # ... (logique similaire)
    # ASSERT
    # ... (vérifications pour le cas critique)
    pass # À compléter pour l'exercice !
