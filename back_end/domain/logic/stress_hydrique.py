# Fichier calcul : domain/logic/stress_hydrique.py

def calculer_bilan_hydrique_simplifie(
    reserve_eau_veille: float,
    pluie_et_arrosage_jour: float,
    evapotranspiration_reference_jour: float,
    reserve_utile_max: float,
    coefficient_cultural: float,
    type_sol: str | None = None,
    type_espace: str | None = None,
) -> tuple[float, float, str]:
    """
    Calcule le statut hydrique d'un sol basé sur un bilan hydrique amélioré.

    Args:
        reserve_eau_veille (float): Réserve en eau du sol de la veille (R_t) en mm.
        pluie_et_arrosage_jour (float): Apports d'eau du jour (P_t) en mm.
        evapotranspiration_reference_jour (float): Évapotranspiration de référence (ET_0,t) en mm.
        reserve_utile_max (float): Réserve utile maximale du sol (R_max) en mm.
        coefficient_cultural (float): Coefficient cultural (K_c) sans unité.
        type_sol (str | None, optional): Type de sol pour ajuster la consommation.
                                         Ex: "riche", "moyen", "pauvre". Defaults to None.
        type_espace (str | None, optional): Type d'espace pour un futur ajustement. Defaults to None.

    Returns:
        tuple[float, float, str]: Un tuple contenant la nouvelle réserve en eau (mm),
                                  l'indice de stress (0 à 1), et le statut textuel.
    """
    # 1. Calcul du besoin théorique de la plante pour la journée (ETc)
    besoin_plante_par_jour = evapotranspiration_reference_jour * coefficient_cultural

    # 2. Déterminer un facteur_sol selon le type de sol
    if type_sol == "riche":
        facteur_sol = 0.8  # Le sol retient mieux l'eau, la plante consomme moins vite la réserve
    elif type_sol == "pauvre":
        facteur_sol = 1.2  # Le sol draine vite, la plante doit puiser plus
    else:  # "moyen" ou non spécifié
        facteur_sol = 1.0

    # 3. Déterminer un facteur_meteo simple (placeholder pour de futures améliorations)
    facteur_meteo = 1.0

    # 4. Consommation ajustée de la journée
    consommation_jour = besoin_plante_par_jour * facteur_sol * facteur_meteo

    # 5. Mise à jour de la réserve brute
    reserve_brute = reserve_eau_veille + pluie_et_arrosage_jour - consommation_jour

    # 6. Bornage de la réserve entre 0 et reserve_utile_max
    nouvelle_reserve = min(reserve_utile_max, max(0, reserve_brute))

    # 7. Calcul du taux de remplissage et de l'indice de stress
    if reserve_utile_max > 0:
        taux_remplissage = nouvelle_reserve / reserve_utile_max
    else:
        taux_remplissage = 0

    indice_stress = 1 - taux_remplissage
    indice_stress = min(1.0, max(0.0, indice_stress))  # On s'assure que l'indice reste bien entre 0 et 1

    # 9. Détermination du statut hydrique à partir de l'indice
    if indice_stress < 0.3:
        statut = "Confort"
    elif indice_stress < 0.6:
        statut = "A surveiller"
    else:  # indice_stress >= 0.6
        statut = "Critique"

    return (nouvelle_reserve, indice_stress, statut)
