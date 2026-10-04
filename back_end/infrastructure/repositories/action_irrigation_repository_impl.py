from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.models import ActionIrrigation
from domain.ports.action_irrigation_repository import IActionIrrigationRepository


class ActionIrrigationRepositoryImpl(IActionIrrigationRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_par_intervention(self, intervention_id: int) -> ActionIrrigation | None:
        return self.db.query(ActionIrrigation).filter(ActionIrrigation.intervention_id == intervention_id).first()

    def ajouter(self, action: ActionIrrigation) -> ActionIrrigation:
        self.db.add(action)
        self.db.flush()
        return action

    def supprimer(self, action: ActionIrrigation) -> None:
        self.db.delete(action)
        self.db.flush()

    def cumul_mm(self, espace_id: int, debut: datetime, fin: datetime) -> float:
        total = (
            self.db.query(func.sum(ActionIrrigation.quantite_mm))
            .filter(ActionIrrigation.espace_id == espace_id,
                    ActionIrrigation.timestamp >= debut, ActionIrrigation.timestamp < fin)
            .scalar()
        )
        return float(total or 0.0)
