# back_end/domain/logic/bilan_carbone.py

from domain.entities import EspaceVertEntity

def estimer_co2_absorbe_jour(
    espace_vert: EspaceVertEntity,
    stress_hydrique: float,
    stress_sanitaire: float | None,
) -> float:
    """
    Estime la quantité de CO2 absorbée (en kg) pour une journée donnée.
    Formule simplifiée : Surface * Facteur de base * (1 - Stress).
    """
    # Facteur de base arbitraire : 0.05 kg/m²/jour pour une plante en bonne santé
    # Ce facteur pourrait dépendre du type_espace ou type_plante à l'avenir.
    facteur_base_kg_m2 = 0.05
    
    # Le stress réduit la photosynthèse
    facteur_stress = (1.0 - stress_hydrique)
    if stress_sanitaire is not None:
        facteur_stress *= (1.0 - stress_sanitaire)
        
    # On s'assure que le facteur reste positif
    facteur_stress = max(0.0, facteur_stress)

    return espace_vert.surface_m2 * facteur_base_kg_m2 * facteur_stress


def estimer_o2_produit_jour(
    espace_vert: EspaceVertEntity,
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