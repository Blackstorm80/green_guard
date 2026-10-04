# Fichier calcul : domain/logic/prevision.py
"""Prévision de la réserve en eau sur 7 jours, date de bascule et décision d'arrosage.

Même moteur que le bilan journalier (fao56.calculer_journee), appliqué jour par jour à partir du
dernier bilan, sans arrosage futur. Calculs purs : aucun accès à la base ni au réseau.

Pluie prévue comptée dans la projection (règle prudente) :
- J (aujourd'hui) : cumul du jour, comme le bilan journalier ;
- J+1 et J+2 (fenêtre de la consigne d'arrosage) : cumul compté seulement si la pluie est « acquise »
  (probabilité ≥ 70 % et cumul ≥ 5 mm), sinon 0. Arroser pour rien coûte moins cher qu'un espace laissé
  sans eau sur une fausse promesse : une pluie seulement probable ne supprime jamais la consigne ;
- J+3 à J+7 (indicatif) : cumul pondéré par la probabilité (espérance), probabilité inconnue = 0.
Le seuil de pluie efficace du moteur (2 mm) s'applique ensuite à la pluie comptée.

Décision (horizon de décision J+3 ; au-delà, la prévision est indicative) :
- « arroser » : bascule en Critique à J+2 ou avant, pluie acquise comprise ; arroser au plus tard la
  veille de la bascule ;
- « reporter » : sans pluie, l'espace basculerait en Critique à J+2 ou avant, mais la pluie acquise des
  48 h le maintient hors Critique jusqu'à J+2 au moins ;
- « surveiller » : bascule en Critique entre J+3 et J+7 ;
- « rien » : aucune bascule en Critique sur 7 jours.
La décision est recalculée à chaque lecture : si la pluie annoncée n'est pas tombée, le bilan du
lendemain le constate et la décision repasse d'elle-même à « arroser ».
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from domain.logic.arrosage import DoseRecommandee, dose_recommandee, formuler_dose
from domain.logic.fao56 import (
    A_SURVEILLER,
    COEFFICIENT_PAYSAGER_DEFAUT,
    CRITIQUE,
    calculer_journee,
    reserve_facilement_utilisable_mm,
    statut_hydrique,
)

HORIZON_JOURS = 7
HORIZON_DECISION_JOURS = 3
DELAI_BASCULE_ARROSER_JOURS = 2
PROBABILITE_PLUIE_ACQUISE_PCT = 70
CUMUL_PLUIE_ACQUISE_MM = 5.0

ARROSER, REPORTER, SURVEILLER, RIEN = "arroser", "reporter", "surveiller", "rien"

AVERTISSEMENT = (
    "Prévision indicative au-delà de J+3 : la décision ne porte que sur les 3 prochains jours. "
    "La probabilité de pluie est régionale (environ 27 km). À J+1 et J+2, une pluie n'est comptée que si "
    "elle est acquise (probabilité d'au moins 70 % et cumul d'au moins 5 mm) ; au-delà, son cumul est "
    "pondéré par sa probabilité."
)

JOURS_SEMAINE = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")
MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre",
        "octobre", "novembre", "décembre")
STATUTS_ORDONNES = {"Optimal": 0, A_SURVEILLER: 1, CRITIQUE: 2}


class PrevisionImpossibleError(ValueError):
    """Pas de point de départ exploitable (bilan absent ou trop ancien) ou prévision météo incomplète."""


class PrevisionMeteoIncompleteError(PrevisionImpossibleError):
    pass


@dataclass(frozen=True)
class EtatHydrique:
    """Point de départ de la projection : termes du dernier bilan FAO-56."""
    date: date
    epuisement_mm: float
    taw_mm: float
    kl: float = COEFFICIENT_PAYSAGER_DEFAUT
    et0_mm: float | None = None
    pluie_mm: float | None = None


@dataclass(frozen=True)
class JourProjete:
    jour: date
    decalage: int                  # 0 = aujourd'hui (J)
    et0_mm: float | None
    pluie_mm: float                # cumul prévu
    probabilite_pluie_pct: float | None
    pluie_comptee_mm: float        # part du cumul retenue par la règle prudente
    pluie_acquise: bool
    epuisement_fin_mm: float
    reserve_mm: float
    reserve_percent: float | None
    statut: str
    indicatif: bool                # au-delà de l'horizon de décision
    issu_du_bilan: bool            # J tiré du bilan du jour plutôt que projeté


@dataclass(frozen=True)
class Decision:
    code: str
    texte: str
    date_limite: date | None = None       # « arroser au plus tard le … »
    jour_pluie: date | None = None        # « reporter » : jour de la pluie attendue
    pluie_attendue_mm: float | None = None
    dose: DoseRecommandee | None = None   # « arroser » : dose au jour limite
    # Mode sécheresse (domain/logic/secheresse.py) : plage à éviter (« 11:00–18:00 ») et dérogation retenue
    plage_interdite: str | None = None
    derogation: str | None = None


@dataclass(frozen=True)
class Prevision:
    jours: list[JourProjete]
    date_bascule_a_surveiller: date | None
    date_bascule_critique: date | None
    decision: Decision
    avertissement: str = AVERTISSEMENT


def pluie_acquise(pluie_mm: float, probabilite_pct: float | None) -> bool:
    return (probabilite_pct is not None and probabilite_pct >= PROBABILITE_PLUIE_ACQUISE_PCT
            and pluie_mm >= CUMUL_PLUIE_ACQUISE_MM)


def pluie_comptee_mm(decalage: int, pluie_mm: float, probabilite_pct: float | None) -> float:
    pluie = max(0.0, pluie_mm)
    if decalage <= 0:
        return pluie
    if decalage <= DELAI_BASCULE_ARROSER_JOURS:
        return pluie if pluie_acquise(pluie, probabilite_pct) else 0.0
    return pluie * min(100.0, max(0.0, probabilite_pct or 0.0)) / 100


def formater_jour(jour: date) -> str:
    """« jeudi 8 octobre »."""
    return f"{JOURS_SEMAINE[jour.weekday()]} {jour.day} {MOIS[jour.month - 1]}"


def _mm(valeur: float) -> str:
    return f"{valeur:.1f}".replace(".", ",").removesuffix(",0")


def _previsions_par_jour(previsions: Sequence[Any], debut: date, fin: date) -> dict[date, Any]:
    par_jour = {p.jour: p for p in previsions}
    attendus = (debut + timedelta(days=i) for i in range((fin - debut).days + 1))
    manquants = [j for j in attendus if j not in par_jour or par_jour[j].et0_mm is None]
    if manquants:
        raise PrevisionMeteoIncompleteError(f"Prévision météo incomplète ({len(manquants)} jour(s) sans ET0)")
    return par_jour


def projeter_reserve(
    etat: EtatHydrique,
    previsions: Sequence[Any],
    aujourd_hui: date,
    avec_pluie: bool = True,
) -> list[JourProjete]:
    """Série J..J+7. Chaque prévision expose jour, et0_mm, pluie_mm, probabilite_pluie_pct.

    Point de départ : bilan du jour (J repris tel quel) ou de la veille (J projeté avec la météo du jour).
    Lève PrevisionImpossibleError si le bilan est plus ancien ou si un jour de prévision manque.
    avec_pluie=False : aucune pluie au-delà de J (scénario sec, pour la décision « reporter »).
    """
    if etat.date not in (aujourd_hui, aujourd_hui - timedelta(days=1)):
        raise PrevisionImpossibleError(f"Dernier bilan trop ancien ({etat.date}) pour projeter la réserve")
    fin = aujourd_hui + timedelta(days=HORIZON_JOURS)
    debut_projection = aujourd_hui if etat.date < aujourd_hui else aujourd_hui + timedelta(days=1)
    par_jour = _previsions_par_jour(previsions, debut_projection, fin)

    taw = max(0.0, etat.taw_mm)
    raw = reserve_facilement_utilisable_mm(taw)
    epuisement = min(taw, max(0.0, etat.epuisement_mm))
    jours: list[JourProjete] = []

    if etat.date == aujourd_hui:
        prevu = par_jour.get(aujourd_hui)
        jours.append(JourProjete(
            jour=aujourd_hui, decalage=0, et0_mm=etat.et0_mm,
            pluie_mm=etat.pluie_mm or 0.0,
            probabilite_pluie_pct=prevu.probabilite_pluie_pct if prevu else None,
            pluie_comptee_mm=etat.pluie_mm or 0.0, pluie_acquise=False,
            epuisement_fin_mm=epuisement, reserve_mm=taw - epuisement,
            reserve_percent=(taw - epuisement) / taw * 100 if taw > 0 else None,
            statut=statut_hydrique(epuisement, taw, raw), indicatif=False, issu_du_bilan=True,
        ))

    jour = debut_projection
    while jour <= fin:
        decalage = (jour - aujourd_hui).days
        prevu = par_jour[jour]
        pluie = max(0.0, prevu.pluie_mm or 0.0)
        comptee = pluie_comptee_mm(decalage, pluie, prevu.probabilite_pluie_pct)
        if not avec_pluie and decalage > 0:
            comptee = 0.0
        termes = calculer_journee(epuisement, prevu.et0_mm, comptee, 0.0, taw, kl=etat.kl)
        epuisement = termes.epuisement_fin_mm
        jours.append(JourProjete(
            jour=jour, decalage=decalage, et0_mm=prevu.et0_mm, pluie_mm=pluie,
            probabilite_pluie_pct=prevu.probabilite_pluie_pct, pluie_comptee_mm=comptee,
            pluie_acquise=decalage > 0 and pluie_acquise(pluie, prevu.probabilite_pluie_pct),
            epuisement_fin_mm=epuisement, reserve_mm=termes.reserve_restante_mm,
            reserve_percent=termes.reserve_restante_mm / taw * 100 if taw > 0 else None,
            statut=termes.statut, indicatif=decalage > HORIZON_DECISION_JOURS, issu_du_bilan=False,
        ))
        jour += timedelta(days=1)
    return jours


def premiere_bascule(jours: Sequence[JourProjete], statut: str) -> date | None:
    """Premier jour où le statut atteint (ou dépasse) celui demandé ; J s'il y est déjà."""
    seuil = STATUTS_ORDONNES[statut]
    return next((j.jour for j in jours if STATUTS_ORDONNES.get(j.statut, 2) >= seuil), None)


def _texte_arroser(aujourd_hui: date, bascule: date, date_limite: date, dose: DoseRecommandee | None) -> str:
    if bascule <= aujourd_hui:
        texte = "Arroser dès aujourd'hui : la réserve est critique."
    elif date_limite == aujourd_hui:
        texte = f"Arroser aujourd'hui au plus tard : critique prévu demain ({formater_jour(bascule)})."
    else:
        texte = f"Arroser au plus tard le {formater_jour(date_limite)} : critique prévu le {formater_jour(bascule)}."
    conseil = formuler_dose(dose)
    return f"{texte} {conseil}" if conseil else texte


def decider(
    jours: Sequence[JourProjete],
    jours_sans_pluie: Sequence[JourProjete],
    aujourd_hui: date,
    taw_mm: float,
    surface_m2: float | None = None,
    type_irrigation: str | None = None,
    debit_l_min: float | None = None,
) -> Decision:
    """Décision à partir de la projection (règle prudente) et du scénario sans pluie (voir module).

    Jusqu'à J+2, la projection ne compte que la pluie acquise : une bascule à J+2 ou avant y impose
    d'arroser, et un report n'est possible que si cette pluie la repousse au-delà de J+2.
    """
    limite_arrosage = aujourd_hui + timedelta(days=DELAI_BASCULE_ARROSER_JOURS)
    bascule = premiere_bascule(jours, CRITIQUE)
    bascule_sans_pluie = premiere_bascule(jours_sans_pluie, CRITIQUE)
    par_jour = {j.jour: j for j in jours}

    if bascule is not None and bascule <= limite_arrosage:
        date_limite = max(aujourd_hui, bascule - timedelta(days=1))
        dose = dose_recommandee(par_jour[date_limite].epuisement_fin_mm, taw_mm, surface_m2, type_irrigation,
                                debit_l_min)
        return Decision(ARROSER, _texte_arroser(aujourd_hui, bascule, date_limite, dose),
                        date_limite=date_limite, dose=dose)

    if bascule_sans_pluie is not None and bascule_sans_pluie <= limite_arrosage:
        pluie = next((j for j in jours if aujourd_hui < j.jour <= limite_arrosage and j.pluie_acquise), None)
        if pluie is not None:
            texte = (f"Reporter l'arrosage : pluie de {_mm(pluie.pluie_mm)} mm attendue "
                     f"{'demain' if pluie.decalage == 1 else formater_jour(pluie.jour)}"
                     f" (probabilité {round(pluie.probabilite_pluie_pct)} %).")
            if bascule is not None and (bascule - aujourd_hui).days <= HORIZON_DECISION_JOURS:
                # La pluie ne fait gagner qu'un jour : le dire plutôt que laisser croire le besoin écarté
                texte += f" Critique prévu ensuite le {formater_jour(bascule)} : à surveiller."
            return Decision(REPORTER, texte, jour_pluie=pluie.jour, pluie_attendue_mm=pluie.pluie_mm)

    if bascule is not None:
        indicatif = (bascule - aujourd_hui).days > HORIZON_DECISION_JOURS
        texte = f"Critique prévu le {formater_jour(bascule)} : à surveiller"
        return Decision(SURVEILLER, texte + (" (prévision indicative)." if indicatif else "."))

    texte = "Aucun besoin d'arrosage prévu sur 7 jours."
    surveillance = premiere_bascule(jours, A_SURVEILLER)
    if surveillance is not None and surveillance > aujourd_hui:
        texte += f" Réserve « à surveiller » à partir du {formater_jour(surveillance)}."
    return Decision(RIEN, texte)


def prevoir(
    etat: EtatHydrique,
    previsions: Sequence[Any],
    aujourd_hui: date,
    surface_m2: float | None = None,
    type_irrigation: str | None = None,
    debit_l_min: float | None = None,
) -> Prevision:
    """Série J..J+7, dates de bascule et décision. Lève PrevisionImpossibleError (voir projeter_reserve)."""
    jours = projeter_reserve(etat, previsions, aujourd_hui)
    jours_sans_pluie = projeter_reserve(etat, previsions, aujourd_hui, avec_pluie=False)
    return Prevision(
        jours=jours,
        date_bascule_a_surveiller=premiere_bascule(jours, A_SURVEILLER),
        date_bascule_critique=premiere_bascule(jours, CRITIQUE),
        decision=decider(jours, jours_sans_pluie, aujourd_hui, etat.taw_mm, surface_m2, type_irrigation,
                         debit_l_min),
    )
