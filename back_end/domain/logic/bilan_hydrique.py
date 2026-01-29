# Fichier : domain/logic/bilan_hydrique.py

import datetime

# Note: Les chemins d'import sont basés sur la structure cible du projet.
from domain.entities import EspaceVertEntity, BilanHydriqueJournalierEntity
from domain.ports.meteo_service import IMeteoService
from domain.logic.stress_hydrique import calculer_bilan_hydrique_simplifie


def _parse_localisation(localisation: str | None) -> tuple[float, float]:
    """Fonction utilitaire pour parser une chaîne "latitude, longitude"."""
    if not localisation:
        return 0.0, 0.0
    try:
        lat_str, lon_str = localisation.split(',')
        return float(lat_str.strip()), float(lon_str.strip())
    except (ValueError, IndexError):
        # Dans une application réelle, on pourrait logger un avertissement ici.
        return 0.0, 0.0


def calculer_bilan_hydrique_pour_jour(
    espace_vert: EspaceVertEntity,
    bilan_veille: BilanHydriqueJournalierEntity | None,
    meteo_service: IMeteoService,
    arrosage_jour_mm: float,
    date_du_jour: datetime.date,
) -> BilanHydriqueJournalierEntity:
    """
    Orchestre le calcul du bilan hydrique pour un espace vert à une date donnée.

    Args:
        espace_vert: L'entité de l'espace vert concerné.
        bilan_veille: Le bilan hydrique calculé la veille. Peut être None si c'est le premier calcul.
        meteo_service: Un service (port) pour obtenir les données météo.
        arrosage_jour_mm: La quantité d'eau d'arrosage ajoutée manuellement ce jour-là (en mm).
        date_du_jour: La date pour laquelle effectuer le calcul.

    Returns:
        Une nouvelle entité BilanHydriqueJournalierEntity avec les résultats du calcul.
    """
    # Étape 1 : Déterminer la réserve en eau de départ.
    # Si c'est le premier calcul, on peut considérer que la réserve est pleine.
    reserve_eau_veille = bilan_veille.reserve_eau if bilan_veille else espace_vert.reserve_utile_max

    # Étape 2 : Récupérer les données météo via le port.
    # NOTE : Nous supposons ici que la localisation est une chaîne "latitude, longitude".
    latitude, longitude = _parse_localisation(espace_vert.localisation)
    donnees_meteo = meteo_service.get_donnees_meteo_jour(
        latitude=latitude, longitude=longitude, date=date_du_jour
    )

    # Étape 3 : Appeler la logique de calcul pure.
    total_apport_eau = donnees_meteo.pluie_mm + arrosage_jour_mm

    nouvelle_reserve, indice_stress, statut = calculer_bilan_hydrique_simplifie(
        reserve_eau_veille=reserve_eau_veille,
        pluie_et_arrosage_jour=total_apport_eau,
        evapotranspiration_reference_jour=donnees_meteo.et0_mm,
        reserve_utile_max=espace_vert.reserve_utile_max,
        coefficient_cultural=espace_vert.coefficient_cultural,
    )

    # Étape 4 : Construire et retourner la nouvelle entité métier.
    # L'ID est mis à 0 pour indiquer une nouvelle entité non persistée.
    nouveau_bilan = BilanHydriqueJournalierEntity(
        id=0,  # Placeholder pour une nouvelle entité
        date=date_du_jour,
        reserve_eau=nouvelle_reserve,
        indice_stress=indice_stress,
        statut_hydrique=statut,
        espace_id=espace_vert.id,
    )

    return nouveau_bilan