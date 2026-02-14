# back_end/application/use_cases/vegetal.py

from domain.ports.espace_vert_repository import IEspaceVertRepository
from domain.ports.bilan_hydrique_repository import IBilanHydriqueRepository
from domain.logic.bilan_carbone import estimer_co2_absorbe_jour, estimer_o2_produit_jour
from application.dto.vegetal import EtatGlobalVegetalDTO, ImpactCarboneDTO, DetailZoneImpactDTO

def calculer_etat_global_vegetal(
    espace_repo: IEspaceVertRepository,
    bilan_repo: IBilanHydriqueRepository
) -> EtatGlobalVegetalDTO:
    """
    Calcule les statistiques globales de santé du parc végétal.
    """
    espaces = espace_repo.list_tous()
    total_espaces = len(espaces)
    
    if total_espaces == 0:
        return EtatGlobalVegetalDTO(
            sante_globale_percent=100.0,
            espaces_en_stress=0,
            total_espaces=0,
            espaces_critique=0,
            espaces_warning=0
        )

    critique_count = 0
    warning_count = 0
    somme_indices_stress = 0.0

    for espace in espaces:
        bilan = bilan_repo.get_dernier_bilan_pour_espace(espace.id)
        if bilan:
            somme_indices_stress += bilan.indice_stress
            if bilan.statut_hydrique == "Critique":
                critique_count += 1
            elif bilan.statut_hydrique == "A surveiller": # ou "Warning" selon votre convention
                warning_count += 1
    
    # Calcul du pourcentage de santé globale (inverse du stress moyen)
    stress_moyen = somme_indices_stress / total_espaces
    sante_globale = max(0.0, (1.0 - stress_moyen) * 100.0)

    return EtatGlobalVegetalDTO(
        sante_globale_percent=round(sante_globale, 1),
        espaces_en_stress=critique_count + warning_count,
        total_espaces=total_espaces,
        espaces_critique=critique_count,
        espaces_warning=warning_count
    )


def calculer_impact_carbone(
    espace_repo: IEspaceVertRepository,
    bilan_repo: IBilanHydriqueRepository
) -> ImpactCarboneDTO:
    """
    Calcule l'impact carbone et oxygène agrégé (journalier estimé).
    """
    espaces = espace_repo.list_tous()
    
    total_co2 = 0.0
    total_o2 = 0.0
    stats_par_zone = {}

    for espace in espaces:
        bilan = bilan_repo.get_dernier_bilan_pour_espace(espace.id)
        
        # Valeurs par défaut si pas de bilan (pas de stress)
        stress_h = bilan.indice_stress if bilan else 0.0
        stress_s = bilan.stress_sanitaire if bilan else 0.0
        
        co2 = estimer_co2_absorbe_jour(espace, stress_h, stress_s)
        o2 = estimer_o2_produit_jour(espace, stress_h, stress_s)
        
        total_co2 += co2
        total_o2 += o2
        
        # Agrégation par zone
        zone = espace.zone or "Non définie"
        if zone not in stats_par_zone:
            stats_par_zone[zone] = {"co2": 0.0, "o2": 0.0}
        stats_par_zone[zone]["co2"] += co2
        stats_par_zone[zone]["o2"] += o2

    # Construction de la liste de détails
    details = [
        DetailZoneImpactDTO(
            zone=z, 
            oxygen_kg=round(vals["o2"], 2), 
            carbon_kg=round(vals["co2"], 2)
        )
        for z, vals in stats_par_zone.items()
    ]

    # Pour l'exemple, on projette sur une année (x365) pour avoir des chiffres significatifs
    # comme dans l'exemple JSON (1234 kg), sinon ce serait très faible par jour.
    facteur_projection = 365.0

    return ImpactCarboneDTO(
        total_oxygen_kg=round(total_o2 * facteur_projection, 1),
        total_carbon_absorbed_kg=round(total_co2 * facteur_projection, 1),
        periode="Projection Annuelle (2025)",
        detail_par_zone=details
    )
