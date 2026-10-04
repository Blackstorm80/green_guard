"""Job planifié : niveau VigiEau du jour, bilan hydrique du jour + relevé de mesures pour chaque espace,
puis alertes (stress critique, arrosage à prévoir selon la prévision à 7 jours, corrigée par le mode
sécheresse : aucun arrosage interdit n'est conseillé).

Niveau VigiEau : relevé une fois par jour et par espace (le passage horaire ne relit que les espaces
encore sans relevé du jour, ce qui retente aussi les échecs de la veille ou de l'heure précédente).

Tant que les capteurs IoT ne sont pas branchés, la mesure est dérivée de la
météo réelle (température, humidité de l'air) et du bilan (humidité du sol).

Le worker sert toutes les organisations : seule leur liste est lue hors contexte RLS,
puis chacune est traitée dans son propre contexte (comme une requête de ses membres).
"""
import logging
from datetime import UTC, date, datetime, tzinfo

from sqlalchemy.orm import Session

from application.use_cases.generer_bilans_hydriques_journaliers import (
    arrosage_journalier,
    bornes_du_jour,
    generer_bilans_hydriques_journaliers,
)
from application.use_cases.prevision import etat_du_bilan, prevoir_espace
from application.use_cases.secheresse import actualiser_restrictions, evaluer_espace, restrictions_en_vigueur
from config import settings
from domain.logic.arrosage import formuler_dose
from domain.logic.droits import ROLES_INTERVENTION
from domain.logic.prevision import ARROSER, PrevisionImpossibleError, formater_jour
from domain.logic.secheresse import LIBELLES_NIVEAU, EvaluationArrosage, appliquer_restriction, regles_depuis_parametres
from domain.models import Mesure, Notification, Organisation, RestrictionSecheresse, User
from domain.ports.meteo import IMeteoService, MeteoIndisponibleError
from domain.ports.vigieau import IVigieauService
from infrastructure.database import SessionLocal
from infrastructure.repositories.action_irrigation_repository_impl import ActionIrrigationRepositoryImpl
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.repositories.restriction_secheresse_repository_impl import RestrictionSecheresseRepositoryImpl
from infrastructure.rls import CLE_ORGANISATION, contournement_rls, definir_organisation
from infrastructure.services.meteo_open_meteo import OpenMeteoService
from infrastructure.services.vigieau import VigieauService

logger = logging.getLogger(__name__)

INTERVALLE_MINUTES = 60
TYPE_ARROSAGE_A_PREVOIR = "arrosage_a_prevoir"
# Durée maximale des appels VigiEau par organisation et par passage : les espaces restants le sont au suivant
BUDGET_RELEVE_VIGIEAU_S = 300


def _destinataires(db: Session, organisation_id: int) -> list[int]:
    """Membres actifs qui peuvent agir sur le terrain (le lecteur n'est pas alerté)."""
    return [id_ for (id_,) in db.query(User.id).filter(
        User.organisation_id == organisation_id, User.is_active.is_(True), User.role.in_(ROLES_INTERVENTION),
    ).order_by(User.id)]


def _notifier_stress_critique(db: Session, resultat, destinataires: list[int], debut_journee: datetime,
                              evaluation: EvaluationArrosage | None = None) -> int:
    """Une notification par espace critique, par destinataire et par jour (pas de rappel horaire).
    Sous interdiction sécheresse totale, le message ne recommande pas l'arrosage."""
    if resultat.bilan.statut_hydrique != "Critique":
        return 0
    message = f"Stress hydrique critique sur « {resultat.espace.nom} » : arrosage recommandé."
    if evaluation is not None and evaluation.interdit_toute_la_journee:
        message = (f"Stress hydrique critique sur « {resultat.espace.nom} » : arrosage interdit "
                   f"({LIBELLES_NIVEAU[evaluation.niveau]}, arrêté sécheresse), sauf dérogation.")
    deja = {id_ for (id_,) in db.query(Notification.user_id).filter(
        Notification.user_id.in_(destinataires), Notification.type == "stress_hydrique",
        Notification.message == message, Notification.cree_le >= debut_journee,
    )}
    nouveaux = [user_id for user_id in destinataires if user_id not in deja]
    db.add_all(Notification(user_id=user_id, type="stress_hydrique", message=message,
                            espace_id=resultat.espace.id) for user_id in nouveaux)
    return len(nouveaux)


def _notifier_arrosage_a_prevoir(db: Session, resultat, destinataires: list[int], meteo_service: IMeteoService,
                                 aujourd_hui: date, debut_journee: datetime,
                                 evaluation: EvaluationArrosage | None = None) -> int:
    """Une notification par espace, par destinataire et par jour quand la prévision conclut « arroser ».

    Un espace déjà critique a reçu l'alerte de stress : pas de second message pour la même action.
    La météo prévue est lue dans le cache du service (un appel par point) ; indisponible : rien n'est émis.
    """
    if not destinataires or resultat.bilan.statut_hydrique == "Critique":
        return 0
    etat = etat_du_bilan(resultat.bilan)
    if etat is None:
        return 0
    try:
        decision = appliquer_restriction(prevoir_espace(resultat.espace, etat, meteo_service, aujourd_hui).decision,
                                         evaluation, aujourd_hui)
    except (MeteoIndisponibleError, PrevisionImpossibleError) as exc:
        logger.info("Prévision indisponible pour l'espace %s : %s", resultat.espace.id, exc)
        return 0
    except Exception:
        # Alerte secondaire : son échec ne doit pas annuler les bilans, mesures et alertes de stress
        logger.exception("Échec de la prévision de l'espace %s (worker)", resultat.espace.id)
        return 0
    if decision.code != ARROSER:
        return 0
    deja = {id_ for (id_,) in db.query(Notification.user_id).filter(
        Notification.user_id.in_(destinataires), Notification.type == TYPE_ARROSAGE_A_PREVOIR,
        Notification.espace_id == resultat.espace.id, Notification.cree_le >= debut_journee,
    )}
    quand = "aujourd'hui" if decision.date_limite <= aujourd_hui else f"le {formater_jour(decision.date_limite)}"
    message = f"Arrosage à prévoir sur « {resultat.espace.nom} » au plus tard {quand}."
    conseil = formuler_dose(decision.dose)
    if conseil:
        message += f" {conseil}"
    nouveaux = [user_id for user_id in destinataires if user_id not in deja]
    db.add_all(Notification(user_id=user_id, type=TYPE_ARROSAGE_A_PREVOIR, message=message,
                            espace_id=resultat.espace.id) for user_id in nouveaux)
    return len(nouveaux)


def _relever_restrictions(db: Session, espaces: list, vigieau_service: IVigieauService, aujourd_hui: date,
                          maintenant: datetime) -> dict[int, RestrictionSecheresse]:
    """Niveau du jour des espaces qui n'en ont pas encore ; un échec n'empêche ni les bilans ni les alertes."""
    repo = RestrictionSecheresseRepositoryImpl(db)
    try:
        rapport = actualiser_restrictions(espaces, repo, vigieau_service, aujourd_hui, maintenant,
                                          seulement_manquants=True, liberer=db.commit,
                                          budget_s=BUDGET_RELEVE_VIGIEAU_S)
        db.commit()
        if rapport.echecs:
            logger.warning("Niveau VigiEau du jour manquant pour %d espace(s).", rapport.echecs)
    except Exception:
        db.rollback()
        logger.exception("Échec du relevé des niveaux VigiEau.")
    return restrictions_en_vigueur([e.id for e in espaces], aujourd_hui, repo)


def _mettre_a_jour_organisation(db: Session, organisation_id: int, meteo_service: IMeteoService,
                                maintenant: datetime, fuseau: tzinfo,
                                vigieau_service: IVigieauService) -> tuple[int, int, int]:
    aujourd_hui = maintenant.astimezone(fuseau).date()
    espaces = EspaceVertRepositoryImpl(db).list_par_organisation(organisation_id)
    restrictions = _relever_restrictions(db, espaces, vigieau_service, aujourd_hui, maintenant)
    organisation = db.get(Organisation, organisation_id)
    regles = regles_depuis_parametres(organisation.parametres if organisation else None)
    rapport = generer_bilans_hydriques_journaliers(
        espaces=espaces,
        bilan_repo=BilanHydriqueRepositoryImpl(db),
        meteo_service=meteo_service,
        arrosage_du_jour_mm=arrosage_journalier(ActionIrrigationRepositoryImpl(db), fuseau),
        fuseau=fuseau,
        maintenant=maintenant,
    )

    debut_journee, _ = bornes_du_jour(aujourd_hui, fuseau)
    destinataires = _destinataires(db, organisation_id)
    notifications = 0
    for resultat in rapport.traites:
        # Humidité simulée : part de la réserve utile totale (TAW) encore disponible
        humidite_sol = (1.0 - resultat.bilan.indice_stress) * 100
        db.add(Mesure(
            espace_id=resultat.espace.id,
            temperature=resultat.conditions.temperature_c,
            humidite_sol=round(max(0.0, min(100.0, humidite_sol)), 1),
            humidite_air=resultat.conditions.humidite,
            timestamp=maintenant,
        ))
        evaluation = evaluer_espace(resultat.espace, restrictions.get(resultat.espace.id), regles, aujourd_hui)
        notifications += _notifier_stress_critique(db, resultat, destinataires, debut_journee, evaluation)
        notifications += _notifier_arrosage_a_prevoir(db, resultat, destinataires, meteo_service, aujourd_hui,
                                                      debut_journee, evaluation)
    db.commit()
    return len(rapport.traites), len(rapport.ignores), notifications


def executer_mise_a_jour(db: Session, meteo_service: IMeteoService | None = None,
                         maintenant: datetime | None = None, vigieau_service: IVigieauService | None = None) -> None:
    fuseau = settings.fuseau
    maintenant = maintenant or datetime.now(UTC)
    meteo_service = meteo_service or OpenMeteoService()
    vigieau_service = vigieau_service or VigieauService()

    with contournement_rls(db):
        organisations = [id_ for (id_,) in db.query(Organisation.id).order_by(Organisation.id)]

    contexte_initial = db.info.get(CLE_ORGANISATION)
    traites = ignores = notifications = 0
    try:
        for organisation_id in organisations:
            definir_organisation(db, organisation_id)
            try:
                t, i, n = _mettre_a_jour_organisation(db, organisation_id, meteo_service, maintenant, fuseau,
                                                      vigieau_service)
            except Exception:
                # Une organisation en échec ne prive pas les autres de leur bilan
                db.rollback()
                logger.exception("Échec de la mise à jour de l'organisation %s.", organisation_id)
                continue
            traites, ignores, notifications = traites + t, ignores + i, notifications + n
    finally:
        definir_organisation(db, contexte_initial)

    logger.info("Mise à jour capteurs : %d organisation(s), %d espace(s) traité(s), %d ignoré(s), "
                "%d notification(s).", len(organisations), traites, ignores, notifications)


def run_update() -> None:
    """Point d'entrée du scheduler : ne laisse jamais une exception tuer le job, mais la journalise."""
    db = SessionLocal()
    try:
        executer_mise_a_jour(db)
    except Exception:
        db.rollback()
        logger.exception("Échec de la mise à jour planifiée des capteurs.")
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_update()
