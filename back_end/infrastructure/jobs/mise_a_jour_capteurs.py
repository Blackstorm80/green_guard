"""Job planifié : bilan hydrique du jour + relevé de mesures pour chaque espace.

Tant que les capteurs IoT ne sont pas branchés, la mesure est dérivée de la
météo réelle (température, humidité de l'air) et du bilan (humidité du sol).

Le worker sert toutes les organisations : seule leur liste est lue hors contexte RLS,
puis chacune est traitée dans son propre contexte (comme une requête de ses membres).
"""
import logging
from datetime import UTC, date, datetime, time, timedelta, tzinfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from application.use_cases.generer_bilans_hydriques_journaliers import generer_bilans_hydriques_journaliers
from config import settings
from domain.logic.droits import ROLES_INTERVENTION
from domain.models import ActionIrrigation, Mesure, Notification, Organisation, User
from domain.ports.meteo import IMeteoService
from infrastructure.database import SessionLocal
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.rls import CLE_ORGANISATION, contournement_rls, definir_organisation
from infrastructure.services.meteo_open_meteo import OpenMeteoService

logger = logging.getLogger(__name__)

INTERVALLE_MINUTES = 60


def _bornes_du_jour(jour: date, fuseau: tzinfo) -> tuple[datetime, datetime]:
    """Minuit local du jour et du lendemain, en UTC (heures stockées en UTC)."""
    debut = datetime.combine(jour, time.min, tzinfo=fuseau)
    fin = datetime.combine(jour + timedelta(days=1), time.min, tzinfo=fuseau)
    return debut.astimezone(UTC), fin.astimezone(UTC)


def _arrosage_du_jour(db: Session, fuseau: tzinfo):
    def cumul(espace_id: int, jour: date) -> float:
        debut, fin = _bornes_du_jour(jour, fuseau)
        total = (
            db.query(func.sum(ActionIrrigation.quantite_mm))
            .filter(ActionIrrigation.espace_id == espace_id,
                    ActionIrrigation.timestamp >= debut, ActionIrrigation.timestamp < fin)
            .scalar()
        )
        return float(total or 0.0)
    return cumul


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
    db.add_all(Notification(user_id=user_id, type="stress_hydrique", message=message) for user_id in nouveaux)
    return len(nouveaux)


def _mettre_a_jour_organisation(db: Session, organisation_id: int, meteo_service: IMeteoService,
                                maintenant: datetime, fuseau: tzinfo) -> tuple[int, int, int]:
    rapport = generer_bilans_hydriques_journaliers(
        espaces=EspaceVertRepositoryImpl(db).list_par_organisation(organisation_id),
        bilan_repo=BilanHydriqueRepositoryImpl(db),
        meteo_service=meteo_service,
        arrosage_du_jour_mm=_arrosage_du_jour(db, fuseau),
        fuseau=fuseau,
        maintenant=maintenant,
    )

    debut_journee, _ = _bornes_du_jour(maintenant.astimezone(fuseau).date(), fuseau)
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
