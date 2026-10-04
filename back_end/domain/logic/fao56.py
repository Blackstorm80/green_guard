# Fichier calcul : domain/logic/fao56.py
"""Moteur hydrique FAO-56 « paysager » : bilan journalier de l'épuisement de la zone racinaire.

Référence : Allen R.G., Pereira L.S., Raes D., Smith M. (1998), « Crop evapotranspiration »,
FAO Irrigation and Drainage Paper 56, chapitre 8 (équations 82 à 86). Le coefficient cultural
est remplacé par un coefficient paysager KL (méthode WUCOLS, Costello & Jones, 2014).

Calculs purs : aucun accès à la base ni au réseau. Toutes les hauteurs d'eau sont en mm.
Les tables (sols, profondeurs) restent à faire valider par un agronome partenaire.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

VERSION_MODELE = "fao56-paysager-1"

# Eau utile Δθ = θFC − θWP (m³/m³) : FAO-56 tableau 19, milieu de la fourchette de chaque texture
EAU_UTILE_PAR_TEXTURE = {
    "sableux": 0.08,          # sable : 0,05 à 0,11
    "limoneux": 0.155,        # limon (loam) : 0,13 à 0,18
    "limon-argileux": 0.155,  # limon argilo-fin (silty clay loam) : 0,13 à 0,18
    "argileux": 0.16,         # argile : 0,12 à 0,20
}
ALIAS_TEXTURE = {"sable": "sableux", "limon": "limoneux", "argile": "argileux"}
# Texture non renseignée : valeur intermédiaire prudente (entre sable limoneux et limon)
EAU_UTILE_DEFAUT = 0.14

# Profondeur racinaire efficace Zr (m) par type d'espace. Valeurs paysagères (racines limitées par
# le compactage urbain), plus faibles que les profondeurs agricoles maximales de FAO-56 tableau 22.
PROFONDEUR_RACINAIRE_PAR_TYPE = {
    "gazon": 0.3, "pelouse": 0.3, "square": 0.3,
    "jardin": 0.4, "massif": 0.4,
    "parc": 0.5,
    "arbres": 0.8, "arbre": 0.8, "rue": 0.8,
    # Toiture végétalisée extensive : substrat mince (hypothèse hors cahier des charges, à valider)
    "toiture": 0.15,
}
PROFONDEUR_RACINAIRE_DEFAUT = 0.4  # type « Jardin », type par défaut d'un espace

# Fraction facilement utilisable p : FAO-56 tableau 22 (gazon : 0,5), ajustable par appel
FRACTION_FACILEMENT_UTILISABLE = 0.5
# Coefficient paysager par défaut : gazon de saison fraîche (coefficient de référence de l'université de Californie)
COEFFICIENT_PAYSAGER_DEFAUT = 0.8
# Pluie journalière en dessous de laquelle l'eau est interceptée par le feuillage et ré-évaporée
# avant d'atteindre les racines (FAO-56 : une pluie inférieure à ~0,2 ET0 s'évapore en général
# entièrement ; 2 mm couvre une ET0 estivale de 10 mm/j). Au-delà, le ruissellement est négligé :
# l'excès éventuel sort par drainage profond.
SEUIL_PLUIE_EFFICACE_MM = 2.0

OPTIMAL, A_SURVEILLER, CRITIQUE = "Optimal", "A surveiller", "Critique"


def eau_utile_texture(type_sol: str | None) -> float:
    """Δθ (m³/m³) d'une texture saisie dans l'interface (insensible à la casse)."""
    cle = (type_sol or "").strip().lower()
    return EAU_UTILE_PAR_TEXTURE.get(ALIAS_TEXTURE.get(cle, cle), EAU_UTILE_DEFAUT)


def profondeur_racinaire_m(profondeur_cm: float | None, type_espace: str | None) -> float:
    """Zr (m) : profondeur saisie (cm) si renseignée et positive, sinon défaut du type d'espace."""
    if profondeur_cm is not None and profondeur_cm > 0:
        return profondeur_cm / 100
    return PROFONDEUR_RACINAIRE_PAR_TYPE.get((type_espace or "").strip().lower(), PROFONDEUR_RACINAIRE_DEFAUT)


def reserve_utile_totale_mm(
    type_sol: str | None,
    type_espace: str | None,
    profondeur_racinaire_cm: float | None = None,
    reserve_saisie_mm: float | None = None,
) -> float:
    """TAW = Δθ × Zr × 1000 (FAO-56 éq. 82), sauf réserve saisie explicitement (surcharge prioritaire)."""
    if reserve_saisie_mm is not None and reserve_saisie_mm > 0:
        return float(reserve_saisie_mm)
    return eau_utile_texture(type_sol) * profondeur_racinaire_m(profondeur_racinaire_cm, type_espace) * 1000


def reserve_utile_de_l_espace(espace: Any) -> float:
    """TAW d'un espace (entité ou objet équivalent) selon la règle de surcharge ci-dessus."""
    return reserve_utile_totale_mm(
        getattr(espace, "type_sol", None),
        getattr(espace, "type_espace", None),
        getattr(espace, "profondeur_racinaire", None),
        getattr(espace, "reserve_utile_max", None),
    )


def reserve_facilement_utilisable_mm(taw: float, p: float = FRACTION_FACILEMENT_UTILISABLE) -> float:
    """RAW = p × TAW (FAO-56 éq. 83)."""
    return p * taw


def pluie_efficace_mm(pluie_mm: float) -> float:
    return pluie_mm if pluie_mm >= SEUIL_PLUIE_EFFICACE_MM else 0.0


def coefficient_stress(epuisement: float, taw: float, raw: float) -> float:
    """Ks (FAO-56 éq. 84) : 1 tant que Dr ≤ RAW, puis décroît linéairement jusqu'à 0 à Dr = TAW."""
    if epuisement <= raw:
        return 1.0
    if taw <= raw:
        return 0.0
    return max(0.0, (taw - epuisement) / (taw - raw))


def statut_hydrique(epuisement: float, taw: float, raw: float) -> str:
    """Optimal jusqu'à RAW ; « A surveiller » sur la première moitié de [RAW, TAW] ; Critique au-delà."""
    if taw <= 0:
        return CRITIQUE
    if epuisement <= raw:
        return OPTIMAL
    if epuisement <= raw + (taw - raw) / 2:
        return A_SURVEILLER
    return CRITIQUE


@dataclass(frozen=True)
class TermesBilan:
    """Termes conservés d'une journée : Dr_fin = Dr_début − Pe − I + ETc + DP (bilan fermé)."""
    et0_mm: float
    kl: float
    ks: float
    etc_mm: float
    pluie_mm: float
    pluie_efficace_mm: float
    arrosage_mm: float
    drainage_mm: float
    epuisement_debut_mm: float
    epuisement_fin_mm: float
    taw_mm: float
    raw_mm: float
    reserve_restante_mm: float
    indice_stress: float
    statut: str


def calculer_journee(
    epuisement_debut_mm: float,
    et0_mm: float,
    pluie_mm: float,
    arrosage_mm: float,
    taw_mm: float,
    kl: float = COEFFICIENT_PAYSAGER_DEFAUT,
    p: float = FRACTION_FACILEMENT_UTILISABLE,
) -> TermesBilan:
    """Bilan d'une journée (FAO-56 éq. 85-86).

    Ks est évalué sur l'épuisement en début de journée (FAO-56 § 8, calcul journalier).
    ETc est la consommation réelle : bornée par l'eau restante, si bien que le bilan reste fermé.
    """
    taw = max(0.0, taw_mm)
    raw = reserve_facilement_utilisable_mm(taw, p)
    debut = min(taw, max(0.0, epuisement_debut_mm))
    et0, pluie, arrosage = max(0.0, et0_mm), max(0.0, pluie_mm), max(0.0, arrosage_mm)
    pe = pluie_efficace_mm(pluie)
    ks = coefficient_stress(debut, taw, raw)
    etc = et0 * kl * ks

    brut = debut - pe - arrosage + etc
    drainage = max(0.0, -brut)  # eau au-delà de la capacité au champ : perdue sous les racines
    if brut > taw:
        etc -= brut - taw
        brut = taw
    fin = max(0.0, brut)

    return TermesBilan(
        et0_mm=et0, kl=kl, ks=ks, etc_mm=etc, pluie_mm=pluie, pluie_efficace_mm=pe, arrosage_mm=arrosage,
        drainage_mm=drainage, epuisement_debut_mm=debut, epuisement_fin_mm=fin, taw_mm=taw, raw_mm=raw,
        reserve_restante_mm=taw - fin,
        indice_stress=fin / taw if taw > 0 else 1.0,
        statut=statut_hydrique(fin, taw, raw),
    )


def _mm(valeur: float) -> str:
    return f"{valeur:.1f}".replace(".", ",").removesuffix(",0")


def _il_y_a(jours: int) -> str:
    return "aujourd'hui" if jours == 0 else "hier" if jours == 1 else f"il y a {jours} jours"


def expliquer_bilan(historique: Sequence[Any], jours_evapotranspiration: int = 7) -> str | None:
    """Phrase explicative du dernier bilan, à partir de l'historique trié par date croissante.

    Chaque élément expose date, taw_mm, epuisement_debut_mm, epuisement_fin_mm, pluie_efficace_mm,
    etc_mm. None si le dernier bilan est antérieur au modèle FAO-56 (termes inconnus).
    """
    termes = [b for b in historique if b.taw_mm is not None and b.epuisement_fin_mm is not None]
    if not termes or termes[-1] is not historique[-1] or termes[-1].taw_mm <= 0:
        return None
    dernier = termes[-1]
    pourcentage = round((dernier.taw_mm - dernier.epuisement_fin_mm) / dernier.taw_mm * 100)
    phrase = f"Réserve à {pourcentage} %"

    pluvieux = [b for b in termes if (b.pluie_efficace_mm or 0) > 0]
    if pluvieux:
        pluie = pluvieux[-1]
        manque = dernier.epuisement_fin_mm - pluie.epuisement_fin_mm
        quand = _il_y_a((dernier.date - pluie.date).days)
        if pluie is dernier:
            phrase += f" : pluie efficace de {_mm(pluie.pluie_efficace_mm)} mm aujourd'hui"
        else:
            phrase += (f" : il a manqué {_mm(max(0.0, manque))} mm depuis la dernière pluie "
                       f"({_mm(pluie.pluie_efficace_mm)} mm, {quand})")
    else:
        manque = dernier.epuisement_fin_mm - termes[0].epuisement_debut_mm
        phrase += f" : il a manqué {_mm(max(0.0, manque))} mm en {len(termes)} jour(s) sans pluie efficace"

    recents = [b.etc_mm for b in termes[-jours_evapotranspiration:] if b.etc_mm is not None]
    if recents:
        phrase += f" ; évapotranspiration de {_mm(sum(recents) / len(recents))} mm/j"
    return phrase + "."
