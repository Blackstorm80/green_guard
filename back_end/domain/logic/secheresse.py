"""Mode sécheresse : règles d'arrosage selon le niveau VigiEau, dérogations et priorités. Calculs purs.

Règles par défaut, inspirées du « Guide de mise en œuvre des mesures de restriction des usages de l'eau
en période de sécheresse » (ministère de la Transition écologique, mai 2023), pour l'arrosage des
espaces verts publics :
- vigilance : arrosage autorisé (sensibilisation) ;
- alerte : interdit de 11 h à 18 h ;
- alerte renforcée et crise : interdit, sauf dérogation.
Ces valeurs ne remplacent pas l'arrêté préfectoral : chaque arrêté-cadre départemental peut être plus
souple (arrosage nocturne en alerte renforcée) ou plus strict (plages différentes, jeunes plantations sur
3 ans). Elles sont paramétrables par organisation (organisations.parametres["secheresse"]).

Dérogations par défaut : jeunes plantations de moins de 2 ans (arrosage permis hors 11 h–18 h) et eau de
récupération (non prélevée dans la ressource, hors du champ des restrictions).

Niveau inconnu (VigiEau indisponible ou pas encore lu) : l'arrosage n'est pas bloqué, mais signalé.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from typing import Any

from domain.logic.prevision import ARROSER, Decision, formater_jour

AUCUNE, VIGILANCE, ALERTE, ALERTE_RENFORCEE, CRISE = "aucune", "vigilance", "alerte", "alerte_renforcee", "crise"
NIVEAUX_VIGIEAU = (VIGILANCE, ALERTE, ALERTE_RENFORCEE, CRISE)
NIVEAUX = (AUCUNE, *NIVEAUX_VIGIEAU)
INCONNU = "inconnu"   # registre : niveau non disponible au moment de l'arrosage
RANG_NIVEAU = {AUCUNE: 0, VIGILANCE: 1, ALERTE: 2, ALERTE_RENFORCEE: 3, CRISE: 4}
LIBELLES_NIVEAU = {
    AUCUNE: "aucune restriction", VIGILANCE: "vigilance", ALERTE: "alerte",
    ALERTE_RENFORCEE: "alerte renforcée", CRISE: "crise", INCONNU: "niveau inconnu",
}

RESEAU, FORAGE, RECUPERATION, RIVIERE = "reseau", "forage", "recuperation", "riviere"
SOURCES_EAU = (RESEAU, FORAGE, RECUPERATION, RIVIERE)
# Type de zone d'alerte VigiEau de la ressource prélevée : eau potable (AEP), souterraine (SOU),
# superficielle (SUP). Eau de récupération : aucune ressource prélevée, la zone la plus sévère est affichée.
TYPE_ZONE_PAR_SOURCE = {RESEAU: "AEP", FORAGE: "SOU", RIVIERE: "SUP", RECUPERATION: None}

JEUNES_PLANTATIONS_ANS_MAX = 10
CLE_PARAMETRES = "secheresse"   # clé des règles dans organisations.parametres
SOURCE_REGLES = ("Valeurs par défaut : guide national de mise en œuvre des mesures de restriction des usages de "
                 "l'eau en période de sécheresse (ministère de la Transition écologique, mai 2023). À ajuster selon "
                 "l'arrêté-cadre départemental : l'arrêté préfectoral en vigueur fait foi.")

INTERDIT = "interdit"   # code de décision : besoin d'arrosage, mais arrosage interdit

# Priorité de l'eau disponible : jeunes plantations, puis arbres, puis massifs, puis le reste (gazons)
PRIORITE_JEUNES_PLANTATIONS, PRIORITE_ARBRES, PRIORITE_MASSIFS, PRIORITE_AUTRES = 1, 2, 3, 4
LIBELLES_PRIORITE = {
    PRIORITE_JEUNES_PLANTATIONS: "Jeunes plantations", PRIORITE_ARBRES: "Arbres",
    PRIORITE_MASSIFS: "Massifs", PRIORITE_AUTRES: "Gazons et autres",
}
TYPES_ARBRES = {"arbre", "arbres", "rue", "alignement"}
TYPES_MASSIFS = {"massif", "massifs", "jardin"}

PlageHoraire = tuple[time, time]


@dataclass(frozen=True)
class RegleNiveau:
    interdit: bool = False                       # interdit toute la journée
    plage_interdite: PlageHoraire | None = None  # sinon, interdit dans cette plage (heure locale)


@dataclass(frozen=True)
class ReglesSecheresse:
    niveaux: Mapping[str, RegleNiveau] = field(default_factory=lambda: dict(REGLES_NIVEAUX_PAR_DEFAUT))
    # Âge (ans) en deçà duquel une plantation bénéficie d'une dérogation ; None : dérogation désactivée
    jeunes_plantations_ans: float | None = 2
    plage_interdite_jeunes_plantations: PlageHoraire | None = (time(11), time(18))
    eau_recuperation: bool = True

    def regle(self, niveau: str) -> RegleNiveau:
        return self.niveaux.get(niveau, RegleNiveau())


REGLES_NIVEAUX_PAR_DEFAUT = {
    VIGILANCE: RegleNiveau(),
    ALERTE: RegleNiveau(plage_interdite=(time(11), time(18))),
    ALERTE_RENFORCEE: RegleNiveau(interdit=True),
    CRISE: RegleNiveau(interdit=True),
}


@dataclass(frozen=True)
class EvaluationArrosage:
    niveau: str                          # niveau en vigueur (NIVEAUX) ou INCONNU
    autorise: bool                       # au moment évalué (ou dans la journée si aucun moment n'est donné)
    interdit_toute_la_journee: bool
    plage: PlageHoraire | None           # plage à éviter quand l'arrosage reste possible dans la journée
    motif: str
    derogation: str | None = None

    @property
    def plage_interdite(self) -> str | None:
        """« 11:00–18:00 »."""
        return formater_plage(self.plage)


def formater_plage(plage: PlageHoraire | None) -> str | None:
    return f"{plage[0]:%H:%M}–{plage[1]:%H:%M}" if plage else None


def _heure_texte(t: time) -> str:
    return f"{t.hour} h" + (f" {t.minute:02d}" if t.minute else "")


def formater_plage_texte(plage: PlageHoraire) -> str:
    """« 11 h–18 h », « 8 h 30–20 h »."""
    return f"{_heure_texte(plage[0])}–{_heure_texte(plage[1])}"


def formater_plage_intervalle(plage: PlageHoraire) -> str:
    """« de 11 h à 18 h » (phrase affichée dans un motif de refus)."""
    return f"de {_heure_texte(plage[0])} à {_heure_texte(plage[1])}"


def dans_la_plage(moment: time, plage: PlageHoraire) -> bool:
    debut, fin = plage
    return debut <= moment < fin


def ajouter_annees(depart: date, annees: float) -> date:
    """Date calendaire `annees` ans après `depart` (29 février → 28 février) ; la fraction d'année
    est comptée en jours."""
    entieres = int(annees)
    try:
        anniversaire = depart.replace(year=depart.year + entieres)
    except ValueError:
        anniversaire = depart.replace(year=depart.year + entieres, day=28)
    return anniversaire + timedelta(days=round((annees - entieres) * 365.25))


def jeune_plantation(date_plantation: date | None, jour: date, regles: ReglesSecheresse) -> bool:
    """Moins de N ans : la dérogation cesse le jour du N-ième anniversaire de la plantation."""
    if date_plantation is None or regles.jeunes_plantations_ans is None or regles.jeunes_plantations_ans <= 0:
        return False
    return date_plantation <= jour < ajouter_annees(date_plantation, regles.jeunes_plantations_ans)


def _derogation(source_eau: str | None, date_plantation: date | None, jour: date,
                regles: ReglesSecheresse) -> tuple[str, PlageHoraire | None] | None:
    """Dérogation applicable et plage qui reste interdite ; None sans dérogation."""
    if regles.eau_recuperation and source_eau == RECUPERATION:
        return "Eau de récupération (non prélevée dans la ressource)", None
    if jeune_plantation(date_plantation, jour, regles):
        ans = regles.jeunes_plantations_ans
        duree = f"{ans:g} an" + ("s" if ans >= 2 else "")
        return f"Jeune plantation de moins de {duree}", regles.plage_interdite_jeunes_plantations
    return None


def evaluer_arrosage(
    niveau: str | None,
    regles: ReglesSecheresse,
    jour: date,
    moment: time | None = None,
    source_eau: str | None = RESEAU,
    date_plantation: date | None = None,
) -> EvaluationArrosage:
    """Arrosage permis ou non au niveau en vigueur, à l'heure locale `moment` (None : sur la journée).

    Une dérogation lève l'interdiction totale ou la plage du niveau, en gardant sa propre plage interdite.
    """
    if niveau is None or niveau not in RANG_NIVEAU:
        return EvaluationArrosage(INCONNU, True, False, None,
                                  "Niveau VigiEau inconnu : vérifiez l'arrêté sécheresse en vigueur avant d'arroser.")
    libelle = LIBELLES_NIVEAU[niveau]
    regle = regles.regle(niveau)
    if niveau == AUCUNE or (not regle.interdit and regle.plage_interdite is None):
        motif = ("Aucune restriction sécheresse en vigueur." if niveau == AUCUNE
                 else f"Niveau {libelle} : arrosage autorisé, à limiter au strict nécessaire.")
        return EvaluationArrosage(niveau, True, False, None, motif)

    derogation = _derogation(source_eau, date_plantation, jour, regles)
    if derogation is not None:
        texte, plage = derogation
        if plage is None:
            return EvaluationArrosage(niveau, True, False, None,
                                      f"Niveau {libelle} : arrosage autorisé par dérogation.", texte)
        autorise = moment is None or not dans_la_plage(moment, plage)
        motif = (f"Niveau {libelle} : arrosage autorisé par dérogation, hors {formater_plage_texte(plage)}."
                 if autorise else
                 f"Niveau {libelle} : même par dérogation, l'arrosage est interdit {formater_plage_intervalle(plage)}.")
        return EvaluationArrosage(niveau, autorise, False, plage, motif, texte)

    if regle.interdit:
        return EvaluationArrosage(niveau, False, True, None,
                                  f"Arrosage interdit : niveau {libelle} (arrêté sécheresse), sans dérogation "
                                  "applicable à cet espace.")
    plage = regle.plage_interdite
    autorise = moment is None or not dans_la_plage(moment, plage)
    motif = (f"Niveau {libelle} : arrosage autorisé hors {formater_plage_texte(plage)}." if autorise else
             f"Arrosage interdit {formater_plage_intervalle(plage)} : niveau {libelle} (arrêté sécheresse).")
    return EvaluationArrosage(niveau, autorise, False, plage, motif)


def plage_autorisee(niveau: str | None, plage_interdite: str | None) -> str:
    """Libellé du registre : créneau dans lequel l'arrosage était permis."""
    if niveau in (None, INCONNU):
        return "non vérifiée (niveau inconnu)"
    return f"hors {plage_interdite}" if plage_interdite else "toute la journée"


def priorite_secheresse(type_espace: str | None, date_plantation: date | None, jour: date,
                        regles: ReglesSecheresse) -> int:
    if jeune_plantation(date_plantation, jour, regles):
        return PRIORITE_JEUNES_PLANTATIONS
    type_ = (type_espace or "").strip().lower()
    if type_ in TYPES_ARBRES:
        return PRIORITE_ARBRES
    if type_ in TYPES_MASSIFS:
        return PRIORITE_MASSIFS
    return PRIORITE_AUTRES


def niveau_le_plus_severe(niveaux: list[str]) -> str:
    connus = [n for n in niveaux if n in RANG_NIVEAU]
    return max(connus, key=RANG_NIVEAU.__getitem__) if connus else AUCUNE


#  Paramètres de l'organisation (JSON) ↔ règles
def _heure(valeur: str) -> time:
    heures, minutes = valeur.split(":")
    return time(int(heures), int(minutes))


def _plage(valeur: Any) -> PlageHoraire | None:
    if not valeur:
        return None
    return _heure(valeur["debut"]), _heure(valeur["fin"])


def _ans(valeur: Any) -> float | None:
    """Âge de dérogation lu en base : nombre fini de 0 à JEUNES_PLANTATIONS_ANS_MAX, ou None."""
    if valeur is None:
        return None
    if isinstance(valeur, bool) or not isinstance(valeur, int | float):
        raise TypeError("Âge de dérogation non numérique")
    if not 0 <= valeur <= JEUNES_PLANTATIONS_ANS_MAX:
        raise ValueError("Âge de dérogation hors bornes")
    return valeur


def _booleen(valeur: Any) -> bool:
    if not isinstance(valeur, bool):
        raise TypeError("Booléen attendu")
    return valeur


def _plage_json(plage: PlageHoraire | None) -> dict | None:
    return {"debut": f"{plage[0]:%H:%M}", "fin": f"{plage[1]:%H:%M}"} if plage else None


def regles_depuis_parametres(parametres: Mapping[str, Any] | None) -> ReglesSecheresse:
    """Règles de l'organisation (clé « secheresse », validée à l'écriture) complétées par les défauts.

    Une valeur absente prend la valeur par défaut du guide, champ par champ ; une valeur illisible
    (saisie directe en base) fait retomber sur les défauts : le mode sécheresse ne doit jamais être
    levé par un oubli ou une erreur de paramétrage.
    """
    config = (parametres or {}).get(CLE_PARAMETRES) or {}
    defaut = ReglesSecheresse()
    try:
        niveaux = dict(REGLES_NIVEAUX_PAR_DEFAUT)
        for niveau, regle in (config.get("niveaux") or {}).items():
            if niveau in NIVEAUX_VIGIEAU:
                par_defaut = REGLES_NIVEAUX_PAR_DEFAUT[niveau]
                niveaux[niveau] = RegleNiveau(
                    _booleen(regle["interdit"]) if "interdit" in regle else par_defaut.interdit,
                    _plage(regle["plage_interdite"]) if "plage_interdite" in regle else par_defaut.plage_interdite,
                )
        derogations = config.get("derogations") or {}
        return ReglesSecheresse(
            niveaux=niveaux,
            jeunes_plantations_ans=(_ans(derogations["jeunes_plantations_ans"])
                                    if "jeunes_plantations_ans" in derogations else defaut.jeunes_plantations_ans),
            plage_interdite_jeunes_plantations=(
                _plage(derogations["plage_interdite_jeunes_plantations"])
                if "plage_interdite_jeunes_plantations" in derogations
                else defaut.plage_interdite_jeunes_plantations),
            eau_recuperation=_booleen(derogations.get("eau_recuperation", defaut.eau_recuperation)),
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return defaut


def parametres_depuis_regles(regles: ReglesSecheresse) -> dict[str, Any]:
    return {
        "niveaux": {
            niveau: {"interdit": regle.interdit, "plage_interdite": _plage_json(regle.plage_interdite)}
            for niveau in NIVEAUX_VIGIEAU for regle in [regles.regle(niveau)]
        },
        "derogations": {
            "jeunes_plantations_ans": regles.jeunes_plantations_ans,
            "plage_interdite_jeunes_plantations": _plage_json(regles.plage_interdite_jeunes_plantations),
            "eau_recuperation": regles.eau_recuperation,
        },
    }


#  Décision de la prévision (domain/logic/prevision.py) sous restriction
def appliquer_restriction(decision: Decision, evaluation: EvaluationArrosage | None, aujourd_hui: date) -> Decision:
    """Ne jamais recommander un arrosage interdit : « arroser » devient « interdit » (sans dose) sous
    interdiction totale, ou « arroser hors 11 h–18 h » sous plage interdite. Le niveau du jour est supposé
    toujours en vigueur à la date limite (un arrêté couvre en général plusieurs semaines)."""
    if evaluation is None or decision.code != ARROSER:
        return decision
    if evaluation.interdit_toute_la_journee:
        quand = ("aujourd'hui" if decision.date_limite is None or decision.date_limite <= aujourd_hui
                 else f"le {formater_jour(decision.date_limite)}")
        texte = (f"{evaluation.motif} Ne pas arroser : un arrosage aurait été nécessaire au plus tard {quand}. "
                 "Signaler l'espace si une dérogation peut être demandée.")
        return replace(decision, code=INTERDIT, texte=texte, dose=None)
    texte = decision.texte
    if evaluation.plage is not None:
        texte += f" Arroser hors {formater_plage_texte(evaluation.plage)} ({LIBELLES_NIVEAU[evaluation.niveau]}"
        texte += f", dérogation : {evaluation.derogation.lower()})." if evaluation.derogation else ")."
    elif evaluation.derogation:
        texte += f" Arrosage permis par dérogation : {evaluation.derogation.lower()}."
    elif evaluation.niveau == INCONNU:
        texte += " Niveau VigiEau inconnu : vérifiez l'arrêté sécheresse avant d'arroser."
    return replace(decision, texte=texte, plage_interdite=evaluation.plage_interdite,
                   derogation=evaluation.derogation)
