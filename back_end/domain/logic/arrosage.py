# back_end/domain/logic/arrosage.py

from __future__ import annotations

import math
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from domain.logic.fao56 import reserve_utile_de_l_espace

if TYPE_CHECKING:
    from domain.models import BilanHydriqueJournalier, EspaceVert

# Efficacité d'application : part de l'eau délivrée réellement stockée dans la zone racinaire
EFFICACITE_PAR_IRRIGATION = {
    "goutte-a-goutte": 0.9,
    "aspersion": 0.75,
    "manuel": 0.7,
    "tuyau": 0.7,
}
EFFICACITE_DEFAUT = 0.75
# Tolérance d'horloge entre le terminal de l'agent et le serveur pour une date de réalisation
TOLERANCE_FUTUR_S = 300


class ArrosageNonComptableError(ValueError):
    """L'arrosage saisi ne peut pas être converti en hauteur d'eau pour le bilan."""


class SurfaceInconnueError(ArrosageNonComptableError):
    pass


@dataclass(frozen=True)
class DoseRecommandee:
    """Dose pour ramener la réserve à la capacité au champ : mm au dixième, litres et minutes entiers."""
    mm: float
    litres: float | None
    minutes: float | None


def _normaliser(libelle: str | None) -> str:
    sans_accents = unicodedata.normalize("NFKD", libelle or "").encode("ascii", "ignore").decode()
    return "-".join(sans_accents.lower().replace("_", " ").split())


def efficacite_irrigation(type_irrigation: str | None) -> float:
    """Efficacité du système saisi (« Goutte-à-goutte », « aspersion »…), défaut 0,75 si inconnu."""
    return EFFICACITE_PAR_IRRIGATION.get(_normaliser(type_irrigation), EFFICACITE_DEFAUT)


def quantite_apportee_mm(volume_l: float, surface_m2: float | None) -> float:
    """Hauteur d'eau apportée (1 L/m² = 1 mm). L'efficacité n'est pas déduite : le volume saisi est
    celui réellement versé, et le bilan sort l'excédent par drainage."""
    if surface_m2 is None or surface_m2 <= 0:
        raise SurfaceInconnueError(
            "Surface de l'espace inconnue : renseignez sa surface (m²) pour que l'arrosage soit compté "
            "dans le bilan hydrique."
        )
    return max(0.0, volume_l) / surface_m2


def horodatage_arrosage(realisee_le: datetime, maintenant: datetime) -> datetime:
    """Date de réalisation en UTC (naïve : déjà UTC) ; refusée si elle est dans le futur."""
    horodatage = realisee_le.replace(tzinfo=UTC) if realisee_le.tzinfo is None else realisee_le.astimezone(UTC)
    if (horodatage - maintenant).total_seconds() > TOLERANCE_FUTUR_S:
        raise ArrosageNonComptableError("La date de réalisation d'un arrosage ne peut pas être dans le futur.")
    return horodatage


def dose_recommandee(
    epuisement_mm: float,
    taw_mm: float,
    surface_m2: float | None = None,
    type_irrigation: str | None = None,
    debit_l_min: float | None = None,
) -> DoseRecommandee:
    """Besoin = épuisement Dr (retour à la capacité au champ), plafonné à la TAW.

    litres = besoin × surface / efficacité (None sans surface) ; minutes = litres / débit, arrondies
    à la minute supérieure (None sans débit).
    """
    besoin = min(max(0.0, epuisement_mm), max(0.0, taw_mm))
    litres = None
    if surface_m2 is not None and surface_m2 > 0:
        litres = besoin * surface_m2 / efficacite_irrigation(type_irrigation)
    minutes = None
    if litres is not None and debit_l_min is not None and debit_l_min > 0:
        minutes = float(math.ceil(round(litres / debit_l_min, 6)))
    return DoseRecommandee(
        mm=round(besoin, 1),
        litres=float(round(litres)) if litres is not None else None,
        minutes=minutes,
    )


def _nombre(valeur: float) -> str:
    return f"{valeur:,.1f}".replace(",", " ").replace(".", ",").removesuffix(",0")


def formuler_dose(dose: DoseRecommandee | None) -> str | None:
    """Conseil chiffré du diagnostic ; None si la réserve est pleine ou la dose inconnue."""
    if dose is None or dose.mm <= 0:
        return None
    phrase = f"Pour remplir la réserve : {_nombre(dose.mm)} mm"
    if dose.litres is not None:
        phrase += f", soit {_nombre(dose.litres)} L"
        if dose.minutes is not None:
            phrase += f" ({_nombre(dose.minutes)} min au débit de l'arrosage)"
    return phrase + "."


def calculer_besoin_arrosage_mm(
    espace: EspaceVert,
    bilan: BilanHydriqueJournalier,
    seuil_declenchement_ratio: float = 0.5,
    cible_remplissage_ratio: float = 1.0,
) -> float:
    """
    Calcule la quantité d'eau (en mm) recommandée pour l'arrosage.

    On déclenche l'arrosage si la réserve actuelle est en dessous d'un certain
    pourcentage de la Réserve Utile maximale (RU max), puis on vise un niveau
    cible (par exemple 100 % de la RU).

    Args:
        espace: L'espace vert concerné (pour connaître la réserve utile totale, TAW).
        bilan: Le dernier bilan hydrique (pour connaître la réserve actuelle).
        seuil_declenchement_ratio: Pourcentage de la RU en dessous duquel
            on déclenche l'arrosage (ex: 0.5 pour 50 %).
        cible_remplissage_ratio: Niveau cible de remplissage de la réserve
            (ex: 1.0 pour 100 %).

    Returns:
        La quantité d'eau en mm à apporter. 0.0 si l'arrosage n'est pas nécessaire.
    """
    # éviter les valeurs négatives
    seuil_declenchement_ratio = max(0.0, seuil_declenchement_ratio)
    cible_remplissage_ratio = max(0.0, cible_remplissage_ratio)

    reserve_actuelle = bilan.reserve_utile_fin_journee
    # TAW conservée avec le bilan ; à défaut (bilan historique), celle de l'espace
    ru_max = getattr(bilan, "taw_mm", None) or reserve_utile_de_l_espace(espace)

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
    espace: EspaceVert,
    bilan: BilanHydriqueJournalier,
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
