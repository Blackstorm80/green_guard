# Fichier: domain/logic/compatibilite_plante_espace.py

from typing import Tuple, List
domain.entities import PlanteEntity, EspaceVertEntity


def est_exposition_compatible(
    plante: PlanteEntity,
    espace: EspaceVertEntity,
) -> bool:
    """
    Vérifie si l'exposition réelle de l'espace est compatible
    avec l'exposition souhaitée par la plante.
    """
    p = plante.exposition
    e = espace.exposition_reelle

    # Normaliser si besoin
    p = p.strip().lower()
    e = e.strip().lower()

    # On définit les expositions acceptables pour chaque type de plante
    if p == "soleil":
        expositions_ok = {"soleil", "mi-ombre"}
    elif p == "mi-ombre":
        expositions_ok = {"mi-ombre", "ombre", "soleil"} # Mi-ombre est flexible
    elif p == "ombre":
        expositions_ok = {"ombre", "mi-ombre"}
    else:
        # Si on ne connaît pas l'exposition de la plante, on considère
        # par défaut que tout est acceptable (ou on peut choisir False).
        expositions_ok = {e}

    return e in expositions_ok


def est_sol_compatible(
    plante: PlanteEntity,
    espace: EspaceVertEntity,
) -> bool:
    """
    Vérifie si le type de sol (et éventuellement le pH) de l'espace
    est compatible avec les préférences de la plante.
    Version stricte : le type de sol doit être identique.
    """
    # Type de sol strict
    if espace.type_sol.strip().lower() != plante.type_sol_prefere.strip().lower():
        return False

    # pH : si la plante a des bornes et que l'espace a un pH renseigné
    if plante.ph_min is not None and plante.ph_max is not None and espace.ph_sol is not None:
        if not (plante.ph_min <= espace.ph_sol <= plante.ph_max):
            return False

    # Si on arrive ici, on considère le sol compatible
    return True


def est_climat_compatible(
    plante: PlanteEntity,
    temp_min_site: float | None,
    temp_max_site: float | None,
) -> bool:
    """
    Vérifie si les températures extrêmes du site (si connues)
    sont compatibles avec les limites de survie de la plante.
    Si on n'a pas les données site, on renvoie True (pas de blocage).
    """
    if temp_min_site is not None:
        if temp_min_site < plante.temp_min_survie:
            return False

    if temp_max_site is not None:
        if temp_max_site > plante.temp_max_survie:
            return False

    return True

def verifier_compatibilite_plante_espace(
    plante: PlanteEntity,
    espace: EspaceVertEntity,
    temp_min_site: float | None = None,
    temp_max_site: float | None = None,
) -> Tuple[bool, List[str]]:
    """
    Vérifie la compatibilité globale entre une plante et un espace.
    Retourne (compatible: bool, raisons: list[str]).
    """
    raisons: List[str] = []

    if not est_exposition_compatible(plante, espace):
        raisons.append("Exposition incompatible (plante vs espace).")

    if not est_sol_compatible(plante, espace):
        raisons.append("Type de sol ou pH incompatible avec la plante.")

    if not est_climat_compatible(plante, temp_min_site, temp_max_site):
        raisons.append("Climat (températures extrêmes) incompatible avec la survie de la plante.")

    compatible = len(raisons) == 0
    return compatible, raisons