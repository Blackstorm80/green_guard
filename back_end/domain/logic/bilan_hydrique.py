# Fichier : domain/logic/bilan_hydrique.py

import datetime

from domain.logic.fao56 import (
    COEFFICIENT_PAYSAGER_DEFAUT,
    VERSION_MODELE,
    calculer_journee,
    reserve_utile_de_l_espace,
)
from domain.models import BilanHydriqueJournalier, EspaceVert

# Colonnes recalculées à chaque passage (remplacement idempotent du bilan du jour)
COLONNES_CALCULEES = (
    "reserve_utile_fin_journee", "indice_stress", "statut_hydrique", "stress_sanitaire",
    "et0_mm", "kl", "ks", "etc_mm", "pluie_mm", "pluie_efficace_mm", "arrosage_mm", "drainage_mm",
    "epuisement_debut_mm", "epuisement_fin_mm", "taw_mm", "raw_mm", "version_modele", "source_meteo",
)


def epuisement_initial(bilan_precedent: BilanHydriqueJournalier | None, taw: float) -> float:
    """Épuisement Dr au début du jour, borné à [0, TAW] (la TAW peut avoir changé depuis la veille).

    Premier calcul : réserve pleine. Bilan antérieur au modèle FAO-56 (sans épuisement conservé) :
    on garde sa fraction de réserve consommée (indice de stress), appliquée à la TAW actuelle.
    """
    if bilan_precedent is None:
        return 0.0
    if bilan_precedent.epuisement_fin_mm is not None:
        epuisement = bilan_precedent.epuisement_fin_mm
    else:
        epuisement = (bilan_precedent.indice_stress or 0.0) * taw
    return min(taw, max(0.0, epuisement))


def calculer_bilan_hydrique_pour_jour(
    espace_vert: EspaceVert,
    bilan_precedent: BilanHydriqueJournalier | None,
    pluie_jour_mm: float,
    et0_jour_mm: float,
    arrosage_jour_mm: float,
    date_du_jour: datetime.date,
    stress_sanitaire_jour: float | None,
    source_meteo: str | None = None,
) -> BilanHydriqueJournalier:
    """Bilan FAO-56 du jour, à partir du bilan de la veille (ou d'une réserve pleine)."""
    taw = reserve_utile_de_l_espace(espace_vert)
    termes = calculer_journee(
        epuisement_debut_mm=epuisement_initial(bilan_precedent, taw),
        et0_mm=et0_jour_mm,
        pluie_mm=pluie_jour_mm,
        arrosage_mm=arrosage_jour_mm,
        taw_mm=taw,
        kl=espace_vert.coefficient_cultural or COEFFICIENT_PAYSAGER_DEFAUT,
    )

    return BilanHydriqueJournalier(
        date=date_du_jour,
        espace_id=espace_vert.id,
        reserve_utile_fin_journee=termes.reserve_restante_mm,
        indice_stress=termes.indice_stress,
        statut_hydrique=termes.statut,
        stress_sanitaire=stress_sanitaire_jour,
        et0_mm=termes.et0_mm,
        kl=termes.kl,
        ks=termes.ks,
        etc_mm=termes.etc_mm,
        pluie_mm=termes.pluie_mm,
        pluie_efficace_mm=termes.pluie_efficace_mm,
        arrosage_mm=termes.arrosage_mm,
        drainage_mm=termes.drainage_mm,
        epuisement_debut_mm=termes.epuisement_debut_mm,
        epuisement_fin_mm=termes.epuisement_fin_mm,
        taw_mm=termes.taw_mm,
        raw_mm=termes.raw_mm,
        version_modele=VERSION_MODELE,
        source_meteo=source_meteo,
    )
