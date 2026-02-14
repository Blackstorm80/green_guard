# Fichier : domain/logic/bilan_hydrique.py

import datetime

# Note: Les chemins d'import sont basés sur la structure cible du projet.
from domain.entities import EspaceVertEntity, BilanHydriqueJournalierEntity
from domain.logic.stress_hydrique import calculer_bilan_hydrique_simplifie


def calculer_bilan_hydrique_pour_jour(
    espace_vert: EspaceVertEntity,
    bilan_precedent: BilanHydriqueJournalierEntity | None,
    pluie_jour_mm: float,
    et0_jour_mm: float,
    arrosage_jour_mm: float,
    date_du_jour: datetime.date,
    stress_sanitaire_jour: float | None,
) -> BilanHydriqueJournalierEntity:
    """
    Calcule le bilan hydrique pour un espace vert à une date donnée.
    Cette fonction ne dépend pas de services externes : elle reçoit toutes les valeurs
    nécessaires en paramètres (pluie, ET0, arrosage, stress sanitaire déjà calculé).

    Args:
        espace_vert: L'entité de l'espace vert concerné.
        bilan_precedent: Le bilan hydrique calculé la veille. Peut être None si c'est le premier calcul.
        pluie_jour_mm: Précipitations du jour en mm.
        et0_jour_mm: Évapotranspiration de référence du jour en mm.
        arrosage_jour_mm: La quantité d'eau d'arrosage ajoutée manuellement ce jour-là (en mm).
        date_du_jour: La date pour laquelle effectuer le calcul.
        stress_sanitaire_jour: Le score de stress sanitaire déjà calculé pour la journée (0–1 ou None).

    Returns:
        Une nouvelle entité BilanHydriqueJournalierEntity avec les résultats du calcul.
    """
    # Étape 1 : Déterminer la réserve en eau de départ.
    # Si c'est le premier calcul, on peut considérer que la réserve est pleine.
    reserve_eau_veille = (
        bilan_precedent.reserve_eau
        if bilan_precedent is not None
        else espace_vert.reserve_utile_max
    )

    # Étape 2 : Appeler la logique de calcul du bilan hydrique.
    total_apport_eau = pluie_jour_mm + arrosage_jour_mm

    nouvelle_reserve, indice_stress, statut = calculer_bilan_hydrique_simplifie(
        reserve_eau_veille=reserve_eau_veille,
        pluie_et_arrosage_jour=total_apport_eau,
        evapotranspiration_reference_jour=et0_jour_mm,
        reserve_utile_max=espace_vert.reserve_utile_max,
        coefficient_cultural=espace_vert.coefficient_cultural,
        type_sol=espace_vert.type_sol,
        type_espace=espace_vert.type_espace,
    )

    # 3) Construction de l'entité métier
    nouveau_bilan = BilanHydriqueJournalierEntity(
        id=0,  # id géré par la persistance
        date=date_du_jour,
        reserve_eau=nouvelle_reserve,
        indice_stress=indice_stress,
        statut_hydrique=statut,
        stress_sanitaire=stress_sanitaire_jour,  # Nouveau champ
        espace_id=espace_vert.id,
    )

    return nouveau_bilan