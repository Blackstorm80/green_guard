# back_end/infrastructure/repositories/health_repository.py

from typing import List
from sqlalchemy.orm import Session
from domain.models import Alerte

class HealthRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_alerts(self, alerts: List[Alerte]):
        """
        Enregistre une liste d'objets Alerte en base de données.
        """
        if not alerts:
            return
        
        try:
            self.db.add_all(alerts)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            # Log l'erreur ici
            raise e

    # On pourrait ajouter ici d'autres méthodes liées à la santé,
    # par exemple pour récupérer l'historique des alertes.
