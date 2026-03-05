# Fichier : domain/logic/agregats.py

from dataclasses import dataclass
from typing import List

domain.entities import BilanHydriqueJournalierEntity


@dataclass
class StatutZoneAgrege:
    """DTO pour le statut agrégé d'une zone."""
    statut_global: str  # "excellent", "normal", "warning", "stress"
    ok_count: int
    warning_count: int
    critical_count: int


def calculer_statut_zone(bilans: List[BilanHydriqueJournalierEntity]) -> StatutZoneAgrege:
    """
    Calcule le statut agrégé d'une zone à partir des bilans de ses espaces verts.

    Cette fonction prend une liste de bilans et retourne un statut global
    ainsi que le décompte des espaces dans chaque état.
    """
    if not bilans:
        return StatutZoneAgrege(statut_global="normal", ok_count=0, warning_count=0, critical_count=0)

    ok_count = 0
    warning_count = 0
    critical_count = 0

    for bilan in bilans:
        if bilan.statut_hydrique == "Optimal":
            ok_count += 1
        elif bilan.statut_hydrique == "A surveiller":
            warning_count += 1
        elif bilan.statut_hydrique == "Critique":
            critical_count += 1

    if critical_count > 0:
        statut_global = "stress"
    elif warning_count > 0:
        statut_global = "warning"
    else:
        statut_global = "excellent"

    return StatutZoneAgrege(
        statut_global=statut_global,
        ok_count=ok_count,
        warning_count=warning_count,
        critical_count=critical_count,
    )