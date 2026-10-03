"""Job planifié : bilan hydrique du jour + relevé de mesures pour chaque espace.

Tant que les capteurs IoT ne sont pas branchés, la mesure est dérivée de la
météo réelle (température, humidité de l'air) et du bilan (humidité du sol).
"""
import logging
from datetime import date, datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from application.use_cases.generer_bilans_hydriques_journaliers import generer_bilans_hydriques_journaliers
from domain.models import ActionIrrigation, Mesure
from domain.ports.meteo import IMeteoService
from infrastructure.database import SessionLocal
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.services.meteo_open_meteo import OpenMeteoService

logger = logging.getLogger(__name__)

INTERVALLE_MINUTES = 60


def _arrosage_du_jour(db: Session):
    def cumul(espace_id: int, jour: date) -> float:
        total = (
            db.query(func.sum(ActionIrrigation.quantite_mm))
            .filter(ActionIrrigation.espace_id == espace_id, func.date(ActionIrrigation.timestamp) == jour)
            .scalar()
        )
        return float(total or 0.0)
    return cumul


def executer_mise_a_jour(db: Session, meteo_service: IMeteoService | None = None) -> None:
    rapport = generer_bilans_hydriques_journaliers(
        espaces=EspaceVertRepositoryImpl(db).list_tous(),
        bilan_repo=BilanHydriqueRepositoryImpl(db),
        meteo_service=meteo_service or OpenMeteoService(),
        arrosage_du_jour_mm=_arrosage_du_jour(db),
    )

    maintenant = datetime.now(timezone.utc)
    for resultat in rapport.traites:
        ru_max = resultat.espace.reserve_utile_max or 1.0
        humidite_sol = resultat.bilan.reserve_utile_fin_journee / ru_max * 100
        db.add(Mesure(
            espace_id=resultat.espace.id,
            temperature=resultat.conditions.temperature_c,
            humidite_sol=round(max(0.0, min(100.0, humidite_sol)), 1),
            humidite_air=resultat.conditions.humidite,
            timestamp=maintenant,
        ))
    db.commit()

    logger.info("Mise à jour capteurs : %d espace(s) traité(s), %d ignoré(s).",
                len(rapport.traites), len(rapport.ignores))


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
