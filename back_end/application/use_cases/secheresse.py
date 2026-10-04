"""Mode sécheresse : relevé quotidien du niveau VigiEau par espace, contrôle des arrosages, état et registre.

Le niveau d'un jour est relevé une fois (worker, ou à la demande) puis conservé dans restrictions_secheresse.
Relevé du jour manquant (VigiEau indisponible, worker pas encore passé) : le dernier relevé de moins de
RELEVE_VOISIN_MAX_JOURS jours est repris et signalé comme tel (un arrêté couvre en général plusieurs semaines) ;
sans aucun relevé récent, rien n'est bloqué, le niveau est « inconnu » et signalé (registre compris).
"""
import csv
import io
import logging
import time as horloge
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta, tzinfo
from typing import Any, Protocol

from application.dto.secheresse import (
    EtatEspaceSecheresseDTO,
    EtatSecheresseDTO,
    SecheresseEspaceDTO,
    SyntheseSecheresseDTO,
)
from domain.logic.arrosage import ArrosageNonComptableError, horodatage_arrosage
from domain.logic.prevision import formater_jour
from domain.logic.secheresse import (
    INCONNU,
    LIBELLES_NIVEAU,
    LIBELLES_PRIORITE,
    NIVEAUX,
    RESEAU,
    TYPE_ZONE_PAR_SOURCE,
    EvaluationArrosage,
    ReglesSecheresse,
    evaluer_arrosage,
    niveau_le_plus_severe,
    plage_autorisee,
    priorite_secheresse,
)
from domain.models import Intervention, RestrictionSecheresse
from domain.ports.restriction_secheresse_repository import IRestrictionSecheresseRepository, LigneRegistre
from domain.ports.vigieau import IVigieauService, NiveauVigieau, VigieauIndisponibleError, VigieauInjoignableError

logger = logging.getLogger(__name__)

SOURCE = ("Niveaux : VigiEau (api.vigieau.gouv.fr), au point de chaque espace. Règles par défaut : guide national "
          "sécheresse 2023, paramétrables par l'administrateur ; l'arrêté préfectoral en vigueur fait foi.")
COLONNES_REGISTRE = ("Date/heure", "Espace", "Commune", "Volume (L)", "Niveau VigiEau", "Plage autorisée",
                     "Dérogation", "Zone d'alerte", "Agent")
# Une cellule commençant par l'un de ces caractères serait interprétée comme une formule par un tableur
DEBUTS_FORMULE = ("=", "+", "-", "@", "\t", "\r")
BOM = "\ufeff"
AGENT_INCONNU = "inconnu (compte supprimé ou non renseigné)"
# Erreurs VigiEau successives au-delà desquelles une actualisation cesse d'interroger les espaces suivants
ECHECS_CONSECUTIFS_MAX = 3
# Jour sans relevé : le relevé le plus proche dans cette fenêtre (jours) tient lieu de niveau ; pour aujourd'hui,
# le dernier relevé de la fenêtre (aucun relevé n'est daté du futur)
RELEVE_VOISIN_MAX_JOURS = 7
# Ancienneté maximale (jours) d'une réalisation d'arrosage déclarée : au-delà, le niveau en vigueur ne peut
# plus être établi et l'antidatage permettrait d'échapper à une interdiction
REALISATION_ANTERIEURE_MAX_JOURS = 30


class EspaceSecheresse(Protocol):
    id: int
    nom: str
    latitude: float
    longitude: float


class ArrosageInterditError(ValueError):
    def __init__(self, evaluation: EvaluationArrosage, zone_nom: str | None = None):
        self.evaluation = evaluation
        message = evaluation.motif
        if zone_nom:
            message += f" Zone d'alerte : {zone_nom}."
        super().__init__(message)


@dataclass(frozen=True)
class PointEspace:
    """Ce qu'il faut d'un espace pour interroger VigiEau, copié avant de libérer la session."""
    id: int
    latitude: float
    longitude: float
    source_eau: str | None


@dataclass(frozen=True)
class RapportActualisation:
    lus: int
    echecs: int


def _attribut(espace: Any, nom: str, defaut=None):
    return getattr(espace, nom, defaut)


def jour_et_heure(moment: datetime, fuseau: tzinfo) -> tuple[date, time]:
    """Jour et heure locaux d'un instant (naïf : UTC, comme les dates relues sous SQLite)."""
    local = (moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment).astimezone(fuseau)
    return local.date(), local.time()


def niveau_vigieau(espace: EspaceSecheresse, vigieau: IVigieauService) -> NiveauVigieau:
    """Zone d'alerte de la ressource prélevée par l'espace. Propage VigieauIndisponibleError."""
    type_zone = TYPE_ZONE_PAR_SOURCE.get(_attribut(espace, "source_eau") or RESEAU)
    return vigieau.niveau_au_point(espace.latitude, espace.longitude, type_zone)


def releve_vigieau(espace: EspaceSecheresse, jour: date, repo: IRestrictionSecheresseRepository,
                   vigieau: IVigieauService, maintenant: datetime) -> RestrictionSecheresse:
    """Interroge VigiEau pour l'espace et enregistre le niveau du jour. Propage VigieauIndisponibleError."""
    return repo.enregistrer(espace.id, jour, niveau_vigieau(espace, vigieau), maintenant)


def niveau_du_releve(restriction: RestrictionSecheresse) -> NiveauVigieau:
    return NiveauVigieau(
        niveau=restriction.niveau, type_zone=restriction.type_zone, zone_nom=restriction.zone_nom,
        zone_code=restriction.zone_code, arrete_identifiant=restriction.arrete_identifiant,
        arrete_url=restriction.arrete_url,
    )


def actualiser_restrictions(
    espaces: Sequence[EspaceSecheresse],
    repo: IRestrictionSecheresseRepository,
    vigieau: IVigieauService,
    jour: date,
    maintenant: datetime,
    seulement_manquants: bool = False,
    liberer: Callable[[], None] | None = None,
    budget_s: float | None = None,
) -> RapportActualisation:
    """Relevé du jour de chaque espace (sans valider la transaction).

    seulement_manquants : passage horaire du worker, qui ne relit que les espaces sans relevé du jour.
    Tous les niveaux sont lus avant la première écriture : aucun verrou n'est tenu pendant les appels HTTP.
    liberer : appelé avant le premier appel HTTP (db.commit : la connexion revient au pool pendant les appels,
    au lieu de rester « idle in transaction »).
    VigiEau injoignable, en erreur pour ECHECS_CONSECUTIFS_MAX espaces de suite, ou budget_s secondes
    écoulées (service lent qui répond quand même) : les espaces suivants ne sont pas interrogés.
    """
    deja = repo.par_espaces([e.id for e in espaces], jour) if seulement_manquants else {}
    a_relever = [PointEspace(e.id, e.latitude, e.longitude, _attribut(e, "source_eau"))
                 for e in espaces if e.id not in deja]
    if liberer is not None:
        liberer()
    debut = horloge.monotonic()
    lus: list[tuple[int, NiveauVigieau]] = []
    echecs = consecutifs = 0
    for index, espace in enumerate(a_relever):
        restants = len(a_relever) - index - 1
        if budget_s is not None and horloge.monotonic() - debut >= budget_s:
            logger.warning("Relevé VigiEau interrompu après %.0f s : %d espace(s) non interrogé(s).",
                           budget_s, restants + 1)
            echecs += restants + 1
            break
        try:
            lus.append((espace.id, niveau_vigieau(espace, vigieau)))
            consecutifs = 0
        except VigieauInjoignableError as exc:
            logger.warning("VigiEau injoignable : %d espace(s) sans niveau du jour (%s)", restants + 1, exc)
            echecs += restants + 1
            break
        except VigieauIndisponibleError as exc:
            logger.warning("Niveau VigiEau indisponible pour l'espace %s : %s", espace.id, exc)
            echecs += 1
            consecutifs += 1
            if consecutifs >= ECHECS_CONSECUTIFS_MAX and restants:
                logger.warning("VigiEau en erreur %d fois de suite : %d espace(s) non interrogé(s).",
                               consecutifs, restants)
                echecs += restants
                break
    for espace_id, niveau in lus:
        repo.enregistrer(espace_id, jour, niveau, maintenant)
    if echecs and not lus:
        # Plus aucun niveau lu : panne durable ou changement d'API (un 404 généralisé…) à surveiller
        logger.error("Aucun niveau VigiEau relevé le %s (%d espace(s) en échec) : arrosages non contrôlés.",
                     jour, echecs)
    return RapportActualisation(lus=len(lus), echecs=echecs)


def restriction_du_jour(
    espace: EspaceSecheresse,
    jour: date,
    aujourd_hui: date,
    repo: IRestrictionSecheresseRepository,
    vigieau: IVigieauService | None,
    maintenant: datetime,
) -> RestrictionSecheresse | None:
    """Niveau à retenir pour un jour : le relevé de ce jour ; pour aujourd'hui ou plus tard, celui
    d'aujourd'hui, relevé à la demande s'il manque. Sans relevé du jour (worker en panne, VigiEau
    injoignable) : le relevé le plus proche à RELEVE_VOISIN_MAX_JOURS près, à égalité le plus sévère, pour
    qu'un arrosage (antidaté ou non) n'échappe pas à l'interdiction en vigueur. None : niveau inconnu."""
    jour = min(jour, aujourd_hui)
    restriction = repo.get(espace.id, jour)
    if restriction is None and jour == aujourd_hui and vigieau is not None:
        try:
            restriction = releve_vigieau(espace, jour, repo, vigieau, maintenant)
        except VigieauIndisponibleError as exc:
            logger.warning("Niveau VigiEau indisponible pour l'espace %s : %s", espace.id, exc)
    if restriction is None:
        restriction = repo.plus_proche(espace.id, jour, RELEVE_VOISIN_MAX_JOURS)
    return restriction


def restrictions_en_vigueur(espace_ids: Sequence[int], jour: date,
                            repo: IRestrictionSecheresseRepository) -> dict[int, RestrictionSecheresse]:
    """Relevé du jour de chaque espace ou, à défaut, son dernier relevé de moins de RELEVE_VOISIN_MAX_JOURS
    jours : un arrêté en vigueur hier l'est sans doute encore (ne jamais conseiller un arrosage interdit
    parce que VigiEau ne répond pas)."""
    return repo.en_vigueur(espace_ids, jour, RELEVE_VOISIN_MAX_JOURS)


def evaluer_espace(espace: EspaceSecheresse, restriction: RestrictionSecheresse | None, regles: ReglesSecheresse,
                   jour: date, moment: time | None = None) -> EvaluationArrosage:
    evaluation = evaluer_arrosage(restriction.niveau if restriction else None, regles, jour, moment,
                                  _attribut(espace, "source_eau") or RESEAU, _attribut(espace, "date_plantation"))
    if restriction is not None and restriction.date != jour:
        evaluation = replace(evaluation, motif=f"{evaluation.motif} Niveau relevé le "
                             f"{formater_jour(restriction.date)} (pas de relevé VigiEau ce jour-là).")
    return evaluation


def secheresse_espace(espace: EspaceSecheresse, restriction: RestrictionSecheresse | None,
                      regles: ReglesSecheresse, maintenant_local: datetime) -> SecheresseEspaceDTO:
    jour = maintenant_local.date()
    evaluation = evaluer_espace(espace, restriction, regles, jour, maintenant_local.time())
    priorite = priorite_secheresse(_attribut(espace, "type_espace"), _attribut(espace, "date_plantation"), jour,
                                   regles)
    return SecheresseEspaceDTO(
        niveau=evaluation.niveau, autorise_maintenant=evaluation.autorise,
        interdit_toute_la_journee=evaluation.interdit_toute_la_journee,
        plage_interdite=evaluation.plage_interdite, motif=evaluation.motif, derogation=evaluation.derogation,
        type_zone=restriction.type_zone if restriction else None,
        zone_nom=restriction.zone_nom if restriction else None,
        arrete_url=restriction.arrete_url if restriction else None,
        releve_le=restriction.recupere_le if restriction else None,
        releve_du=restriction.date if restriction else None,
        priorite_secheresse=priorite, priorite_libelle=LIBELLES_PRIORITE[priorite],
    )


def etat_secheresse(
    espaces: Sequence[EspaceSecheresse],
    repo: IRestrictionSecheresseRepository,
    regles: ReglesSecheresse,
    fuseau: tzinfo,
    maintenant: datetime | None = None,
) -> EtatSecheresseDTO:
    """Niveau du jour de chaque espace de l'organisation (relevés déjà en base) et synthèse."""
    local = (maintenant or datetime.now(UTC)).astimezone(fuseau)
    restrictions = restrictions_en_vigueur([e.id for e in espaces], local.date(), repo)
    lignes = []
    for espace in espaces:
        detail = secheresse_espace(espace, restrictions.get(espace.id), regles, local)
        lignes.append(EtatEspaceSecheresseDTO(
            **detail.model_dump(), espace_id=espace.id, nom=espace.nom, ville=_attribut(espace, "ville"),
            source_eau=_attribut(espace, "source_eau") or RESEAU,
        ))
    lignes.sort(key=lambda l: (l.priorite_secheresse, l.nom.lower(), l.espace_id))

    par_niveau = {niveau: 0 for niveau in (*NIVEAUX, INCONNU)}
    for ligne in lignes:
        par_niveau[ligne.niveau] += 1
    inconnus = par_niveau[INCONNU]
    releves = [r.recupere_le for r in restrictions.values() if r.recupere_le is not None]
    repris = sum(1 for r in restrictions.values() if r.date != local.date())
    avertissements = []
    if inconnus:
        avertissements.append(f"Niveau VigiEau inconnu pour {inconnus} espace(s) (service indisponible ou relevé "
                              "pas encore fait) : l'arrosage n'y est pas bloqué, vérifiez l'arrêté en vigueur.")
    if repris:
        avertissements.append(f"Relevé VigiEau du jour manquant pour {repris} espace(s) : leur dernier niveau "
                              "connu est appliqué.")
    avertissement = " ".join(avertissements) or None
    return EtatSecheresseDTO(
        date=local.date(),
        synthese=SyntheseSecheresseDTO(
            niveau_max=niveau_le_plus_severe([l.niveau for l in lignes]),
            par_niveau=par_niveau,
            espaces_interdits=sum(1 for l in lignes if l.interdit_toute_la_journee),
            espaces_avec_plage=sum(1 for l in lignes if l.plage_interdite),
            espaces_niveau_inconnu=inconnus,
            derniere_actualisation=max(releves) if releves else None,
        ),
        espaces=lignes,
        avertissement=avertissement,
        source=SOURCE,
    )


def _vider_registre(intervention: Intervention) -> None:
    intervention.secheresse_niveau = intervention.secheresse_plage_interdite = None
    intervention.secheresse_derogation = intervention.secheresse_zone = None


def annuler_registre(intervention: Intervention) -> None:
    """Arrosage dont la réalisation est annulée : son registre et son agent sont effacés, sans contrôle
    (annuler un arrosage n'en est pas un, et doit rester possible sous interdiction)."""
    _vider_registre(intervention)
    intervention.realisee_par = None


def _zone_registre(restriction: RestrictionSecheresse | None, jour: date) -> str | None:
    """Zone d'alerte du registre ; un niveau repris d'un autre jour (aucun relevé ce jour-là) le dit."""
    if restriction is None:
        return None
    if restriction.date == jour:
        return restriction.zone_nom
    return f"{(restriction.zone_nom or 'zone non renseignée')[:200]} (niveau relevé le {restriction.date.isoformat()})"


def controler_arrosage(
    intervention: Intervention,
    espace: EspaceSecheresse,
    regles: ReglesSecheresse,
    restriction_pour: Callable[[date], RestrictionSecheresse | None],
    fuseau: tzinfo,
    maintenant: datetime,
    agent_id: int | None,
) -> EvaluationArrosage | None:
    """Contrôle un arrosage avant son enregistrement et fige son registre s'il est réalisé.

    Réalisé (terminée) : évalué à sa date de réalisation ; planifié : à sa date prévue, sinon sur la journée.
    Lève ArrosageNonComptableError si la date de réalisation est dans le futur ou plus ancienne que
    REALISATION_ANTERIEURE_MAX_JOURS (une heure déclarée ne doit pas permettre d'échapper à une
    interdiction), ArrosageInterditError si l'arrosage est interdit
    (aucune dérogation applicable). Renvoie None pour une intervention qui n'est pas un arrosage.
    """
    if intervention.type != "arrosage":
        _vider_registre(intervention)
        return None
    terminee = intervention.statut == "terminee"
    if terminee:
        horodatage = horodatage_arrosage(intervention.realisee_le or maintenant, maintenant)
        if maintenant - horodatage > timedelta(days=REALISATION_ANTERIEURE_MAX_JOURS):
            raise ArrosageNonComptableError(
                f"Un arrosage ne peut pas être déclaré réalisé il y a plus de {REALISATION_ANTERIEURE_MAX_JOURS} "
                "jours : le niveau de restriction alors en vigueur ne peut plus être vérifié.")
    moment = (intervention.realisee_le or maintenant) if terminee else intervention.planifiee_le
    if moment is not None:
        jour, heure = jour_et_heure(moment, fuseau)
    else:
        jour, heure = jour_et_heure(maintenant, fuseau)[0], None
    restriction = restriction_pour(jour)
    evaluation = evaluer_espace(espace, restriction, regles, jour, heure)
    zone = _zone_registre(restriction, jour)
    if not evaluation.autorise:
        raise ArrosageInterditError(evaluation, restriction.zone_nom if restriction else None)
    if not terminee:
        annuler_registre(intervention)
        return evaluation
    intervention.secheresse_niveau = evaluation.niveau
    intervention.secheresse_plage_interdite = evaluation.plage_interdite
    intervention.secheresse_derogation = evaluation.derogation
    intervention.secheresse_zone = zone
    if intervention.realisee_par is None:
        intervention.realisee_par = agent_id
    return evaluation


def _cellule(valeur) -> str:
    texte = "" if valeur is None else str(valeur)
    return f"'{texte}" if texte.startswith(DEBUTS_FORMULE) else texte


def _volume(volume_l: float | None) -> str:
    if volume_l is None:
        return ""
    return f"{volume_l:.1f}".replace(".", ",").removesuffix(",0")


def _niveau_registre(niveau: str | None) -> str:
    if niveau is None:
        return "non enregistré (antérieur au registre)"
    return LIBELLES_NIVEAU.get(niveau, niveau)


def meme_instant(a: datetime | None, b: datetime | None) -> bool:
    """Égalité de deux instants, une date naïve valant UTC (dates relues sous SQLite)."""
    if a is None or b is None:
        return a is b
    return (a.replace(tzinfo=UTC) if a.tzinfo is None else a) == (b.replace(tzinfo=UTC) if b.tzinfo is None else b)


def registre_csv(lignes: Sequence[LigneRegistre], fuseau: tzinfo) -> str:
    """CSV pour tableur français : séparateur « ; », virgule décimale, BOM UTF-8 (accents sous Excel)."""
    sortie = io.StringIO()
    sortie.write(BOM)
    ecrivain = csv.writer(sortie, delimiter=";", lineterminator="\r\n")
    ecrivain.writerow(COLONNES_REGISTRE)
    for ligne in lignes:
        jour, heure = jour_et_heure(ligne.realisee_le, fuseau)
        plage = plage_autorisee(ligne.niveau, ligne.plage_interdite) if ligne.niveau else ""
        ecrivain.writerow([_cellule(v) for v in (
            f"{jour.isoformat()} {heure:%H:%M}", ligne.espace, ligne.commune, _volume(ligne.volume_l),
            _niveau_registre(ligne.niveau), plage, ligne.derogation, ligne.zone, ligne.agent or AGENT_INCONNU,
        )])
    return sortie.getvalue()
