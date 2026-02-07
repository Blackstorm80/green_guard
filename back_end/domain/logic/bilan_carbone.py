# Fichier : domain/logic/bilan_carbone.py

from domain.entities.espace_vert import EspaceVertEntity

def estimer_co2_absorbe_jour(
    espace_vert: EspaceVertEntity,
    stress_hydrique: float,
    stress_sanitaire: float | None,
) -> float:
    """
    Estimation de CO2 absorbé (kg/jour).
    Basée sur une valeur de référence par type d'espace / surface,
    puis modulée par les stress.
    """
    # NOTE: Les valeurs de base sont des placeholders.
    # Elles devraient être stockées en configuration ou dans l'entité EspaceVert.
    base_co2_par_m2 = {
        "pelouse": 0.005,
        "massif": 0.01,
        "arbre isolé": 0.05,
        "toit": 0.015,
        "mur": 0.012,
        "jardin": 0.02,
    }.get(espace_vert.type_espace, 0.01)

    base_co2 = base_co2_par_m2 * (espace_vert.surface_m2 or 0)

    facteur_hydrique = 1 - stress_hydrique
    facteur_sanitaire = 1 - (stress_sanitaire or 0)
    facteur_combine = max(0, min(1, facteur_hydrique * facteur_sanitaire))

    return base_co2 * facteur_combine


def estimer_o2_produit_jour(
    espace_vert: EspaceVertEntity,
    stress_hydrique: float,
    stress_sanitaire: float | None,
) -> float:
    """
    Estimation de O2 produit (kg/jour).
    Même principe que pour le CO2. La ratio CO2/O2 est approximativement 32/44.
    """
    co2_absorbe = estimer_co2_absorbe_jour(espace_vert, stress_hydrique, stress_sanitaire)
    
    # Ratio molaire O2/CO2 est de 1. Pour les masses, c'est M(O2)/M(CO2) = 32/44
    ratio_masse_o2_co2 = 32.0 / 44.0
    
    return co2_absorbe * ratio_masse_o2_co2