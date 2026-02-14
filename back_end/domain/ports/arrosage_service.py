# back_end/domain/logic/arrosage.py

from __future__ import annotations

domain.entities import (
    EspaceVertEntity,
    BilanHydriqueJournalierEntity,
)


def calculer_besoin_arrosage_mm(
    espace: EspaceVertEntity,
    bilan: BilanHydriqueJournalierEntity,
    seuil_declenchement_ratio: float = 0.5,
    cible_remplissage_ratio: float = 1.0,
) -> float:
    """
    Calcule la quantité d'eau (en mm) recommandée pour l'arrosage.

    On déclenche l'arrosage si la réserve actuelle est en dessous d'un certain
    pourcentage de la Réserve Utile maximale (RU max), puis on vise un niveau
    cible (par exemple 100 % de la RU).

    Args:
        espace: L'espace vert concerné (pour connaître la Réserve Utile max).
        bilan: Le dernier bilan hydrique (pour connaître la réserve actuelle).
        seuil_declenchement_ratio: Pourcentage de la RU en dessous duquel
            on déclenche l'arrosage (ex: 0.5 pour 50 %).
        cible_remplissage_ratio: Niveau cible de remplissage de la réserve
            (ex: 1.0 pour 100 %).

    Returns:
        La quantité d'eau en mm à apporter. 0.0 si l'arrosage n'est pas nécessaire.
    """
    # Sécurisation minimale des ratios (éviter les valeurs négatives)
    seuil_declenchement_ratio = max(0.0, seuil_declenchement_ratio)
    cible_remplissage_ratio = max(0.0, cible_remplissage_ratio)

    reserve_actuelle = bilan.reserve_eau
    ru_max = espace.reserve_utile_max

    # Seuil en mm (ex: 50 % de 100 mm = 50 mm)
    seuil_mm = ru_max * seuil_declenchement_ratio

    # Si la réserve est au-dessus du seuil, pas besoin d'arroser
    if reserve_actuelle >= seuil_mm:
        return 0.0

    # Sinon, on calcule combien il faut ajouter pour atteindre la cible
    cible_mm = ru_max * cible_remplissage_ratio
    besoin_mm = cible_mm - reserve_actuelle

    # Sécurité : on ne retourne pas de valeur négative
    return max(0.0, besoin_mm)


def convertir_besoin_en_litres(
    besoin_mm: float,
    surface_m2: float,
    efficacite_systeme: float = 0.9,
) -> float:
    """
    Convertit un besoin en hauteur d'eau (mm) en volume (litres),
    en tenant compte de l'efficacité du système d'arrosage.

    Args:
        besoin_mm: Hauteur d'eau requise (1 mm = 1 L/m²).
        surface_m2: Surface de la zone à arroser.
        efficacite_systeme: Facteur d'efficacité (ex: 0.9 pour 90 %).
            Plus l'efficacité est faible, plus il faut délivrer d'eau.

    Returns:
        Le volume d'eau en litres à programmer.
    """
    if besoin_mm <= 0:
        return 0.0

    volume_theorique_litres = besoin_mm * surface_m2

    # Sécurisation de l'efficacité pour éviter division par zéro ou négative
    if efficacite_systeme <= 0:
        # On pourrait aussi lever une exception métier ici
        return volume_theorique_litres

    return volume_theorique_litres / efficacite_systeme


def calculer_volume_arrosage(
    espace: EspaceVertEntity,
    bilan: BilanHydriqueJournalierEntity,
    seuil_declenchement_ratio: float = 0.5,
    cible_remplissage_ratio: float = 1.0,
    efficacite_systeme: float = 0.9,
) -> float:
    """
    Calcule directement le volume d'arrosage (en litres) à partir de
    l'espace, du bilan et des paramètres de pilotage.
    """
    besoin_mm = calculer_besoin_arrosage_mm(
        espace=espace,
        bilan=bilan,
        seuil_declenchement_ratio=seuil_declenchement_ratio,
        cible_remplissage_ratio=cible_remplissage_ratio,
    )

    return convertir_besoin_en_litres(
        besoin_mm=besoin_mm,
        surface_m2=espace.surface_m2,
        efficacite_systeme=efficacite_systeme,
    )
