# Fichier calcul : domain/logic/stress_hydrique.py

def calculer_bilan_hydrique_simplifie(
    reserve_eau_veille: float,
    pluie_et_arrosage_jour: float,
    evapotranspiration_reference_jour: float,
    reserve_utile_max: float,
    coefficient_cultural: float,
) -> tuple[float, float, str]:
    """
    Calcule le statut hydrique d'un sol basé sur un bilan hydrique simplifié.

    Args:
        reserve_eau_veille (float): Réserve en eau du sol de la veille (R_t) en mm.
        pluie_et_arrosage_jour (float): Apports d'eau du jour (P_t) en mm.
        evapotranspiration_reference_jour (float): Évapotranspiration de référence (ET_0,t) en mm.
        reserve_utile_max (float): Réserve utile maximale du sol (R_max) en mm.
        coefficient_cultural (float): Coefficient cultural (K_c) sans unité.

    Returns:
        tuple[float, float, str]: Un tuple contenant la nouvelle réserve en eau (mm),
                                  l'indice de stress (0 à 1), et le statut textuel.
    """
    # 1. Calculer l'évapotranspiration de la culture (ETc)
    evapotranspiration_culture = coefficient_cultural * evapotranspiration_reference_jour

    # 2. Calculer la nouvelle réserve en eau du sol (R_{t+1})
    nouvelle_reserve_brute = reserve_eau_veille + pluie_et_arrosage_jour - evapotranspiration_culture
    nouvelle_reserve = min(reserve_utile_max, max(0, nouvelle_reserve_brute))

    # 3. Calculer l'indice de stress hydrique (S_t)
    if reserve_utile_max <= 0:
        # Si le sol ne peut rien retenir, il est en stress permanent par définition.
        indice_stress = 1.0
    else:
        indice_stress = 1 - (nouvelle_reserve / reserve_utile_max)

    # 4. Déterminer le statut à partir de l'indice de stress
    if indice_stress < 0.3:
        statut = "Optimal"
    elif 0.3 <= indice_stress < 0.7:
        statut = "A surveiller"
    else:  # indice_stress >= 0.7
        statut = "Critique"

    return (nouvelle_reserve, indice_stress, statut)

