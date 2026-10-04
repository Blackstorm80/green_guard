# back_end/domain/logic/bilan_carbone.py

from domain.models import EspaceVert

# Nowak D. J. & Crane D. E. (2002), « Carbon storage and sequestration by urban trees in the USA »,
# Environmental Pollution 116(3), p. 381-389 : séquestration brute des arbres urbains
# ≈ 0,306 kg de carbone par m² de couvert arboré et par an.
SEQUESTRATION_C_KG_M2_AN = 0.306
RAPPORT_MASSE_CO2_C = 44.0 / 12.0
CO2_KG_M2_AN = SEQUESTRATION_C_KG_M2_AN * RAPPORT_MASSE_CO2_C  # ≈ 1,12 kg CO2/m²/an
CO2_KG_M2_JOUR = CO2_KG_M2_AN / 365.0

METHODE_CARBONE = (
    "Majorant : surface supposée entièrement couverte d'arbres, séquestration de 0,306 kg C/m²/an "
    "(Nowak & Crane, 2002) soit ≈ 1,12 kg CO2/m²/an, réduite par le stress hydrique et sanitaire du jour."
)


def estimer_co2_absorbe_jour(
    espace_vert: EspaceVert,
    stress_hydrique: float,
    stress_sanitaire: float | None,
) -> float:
    """
    Estime la quantité de CO2 absorbée (en kg) pour une journée donnée : estimation grossière,
    majorante (pelouses et massifs séquestrent bien moins qu'un couvert arboré).
    Formule : Surface × CO2_KG_M2_JOUR × (1 - stress).
    """
    # Le stress réduit la photosynthèse
    facteur_stress = (1.0 - stress_hydrique)
    if stress_sanitaire is not None:
        facteur_stress *= (1.0 - stress_sanitaire)

    # On s'assure que le facteur reste positif
    facteur_stress = max(0.0, facteur_stress)

    return (espace_vert.surface_m2 or 0.0) * CO2_KG_M2_JOUR * facteur_stress


def estimer_o2_produit_jour(
    espace_vert: EspaceVert,
    stress_hydrique: float,
    stress_sanitaire: float | None,
) -> float:
    """
    Estime la quantité d'O2 produite (en kg) pour une journée donnée.
    Approximation : O2 produit ≈ CO2 absorbé * (32/44) (rapport des masses molaires).
    """
    co2 = estimer_co2_absorbe_jour(espace_vert, stress_hydrique, stress_sanitaire)

    # Rapport molaire O2 (32g/mol) / CO2 (44g/mol) ≈ 0.727
    ratio_masse = 32.0 / 44.0

    return co2 * ratio_masse
