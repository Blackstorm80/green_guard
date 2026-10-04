"""Job planifié : bilan hydrique du jour + relevé de mesures pour chaque espace, puis alertes
(stress critique, arrosage à prévoir selon la prévision à 7 jours).

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
from config import settings
from domain.logic.arrosage import formuler_dose
from domain.logic.droits import ROLES_INTERVENTION
from domain.logic.prevision import ARROSER, PrevisionImpossibleError, formater_jour
from domain.models import Mesure, Notification, Organisation, User
from domain.ports.meteo import IMeteoService, MeteoIndisponibleError
from infrastructure.database import SessionLocal
from infrastructure.repositories.action_irrigation_repository_impl import ActionIrrigationRepositoryImpl
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.rls import CLE_ORGANISATION, contournement_rls, definir_organisation
from infrastructure.services.meteo_open_meteo import OpenMeteoService

logger = logging.getLogger(__name__)

INTERVALLE_MINUTES = 60
TYPE_ARROSAGE_A_PREVOIR = "arrosage_a_prevoir"


def _destinataires(db: Session, organisation_id: int) -> list[int]:
    """Membres actifs qui peuvent agir sur le terrain (le lecteur n'est pas alerté)."""
    return [id_ for (id_,) in db.query(User.id).filter(
        User.organisation_id == organisation_id, User.is_active.is_(True), User.role.in_(ROLES_INTERVENTION),
    ).order_by(User.id)]


def _notifier_stress_critique(db: Session, resultat, destinataires: list[int], debut_journee: datetime) -> int:
    """Une notification par espace critique, par destinataire et par jour (pas de rappel horaire)."""
    if resultat.bilan.statut_hydrique != "Critique":
        return 0
    message = f"Stress hydrique critique sur « {resultat.espace.nom} » : arrosage recommandé."
    deja = {id_ for (id_,) in db.query(Notification.user_id).filter(
        Notification.user_id.in_(destinataires), Notification.type == "stress_hydrique",
        Notification.message == message, Notification.cree_le >= debut_journee,
    )}
    nouveaux = [user_id for user_id in destinataires if user_id not in deja]
    db.add_all(Notification(user_id=user_id, type="stress_hydrique", message=message,
                            espace_id=resultat.espace.id) for user_id in nouveaux)
    return len(nouveaux)


def _notifier_arrosage_a_prevoir(db: Session, resultat, destinataires: list[int], meteo_service: IMeteoService,
                                 aujourd_hui: date, debut_journee: datetime) -> int:
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
        decision = prevoir_espace(resultat.espace, etat, meteo_service, aujourd_hui).decision
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


def _mettre_a_jour_organisation(db: Session, organisation_id: int, meteo_service: IMeteoService,
                                maintenant: datetime, fuseau: tzinfo) -> tuple[int, int, int]:
    rapport = generer_bilans_hydriques_journaliers(
        espaces=EspaceVertRepositoryImpl(db).list_par_organisation(organisation_id),
        bilan_repo=BilanHydriqueRepositoryImpl(db),
        meteo_service=meteo_service,
        arrosage_du_jour_mm=arrosage_journalier(ActionIrrigationRepositoryImpl(db), fuseau),
        fuseau=fuseau,
        maintenant=maintenant,
    )

    aujourd_hui = maintenant.astimezone(fuseau).date()
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
        notifications += _notifier_stress_critique(db, resultat, destinataires, debut_journee)
        notifications += _notifier_arrosage_a_prevoir(db, resultat, destinataires, meteo_service, aujourd_hui,
                                                      debut_journee)
    db.commit()
    return len(rapport.traites), len(rapport.ignores), notifications


def executer_mise_a_jour(db: Session, meteo_service: IMeteoService | None = None,
                         maintenant: datetime | None = None) -> None:
    fuseau = settings.fuseau
    maintenant = maintenant or datetime.now(UTC)
    meteo_service = meteo_service or OpenMeteoService()

    with contournement_rls(db):
        organisations = [id_ for (id_,) in db.query(Organisation.id).order_by(Organisation.id)]

    contexte_initial = db.info.get(CLE_ORGANISATION)
    traites = ignores = notifications = 0
    try:
        for organisation_id in organisations:
            definir_organisation(db, organisation_id)
            try:
                t, i, n = _mettre_a_jour_organisation(db, organisation_id, meteo_service, maintenant, fuseau)
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
