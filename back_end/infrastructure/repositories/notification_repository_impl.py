# back_end/infrastructure/repositories/notification_repository_impl.py
from typing import List
from datetime import datetime, timedelta

from domain.ports.notification import INotificationRepository
from domain.entities.notification import NotificationEntity

class NotificationRepositoryImpl(INotificationRepository):
    """
    Implémentation FAKE du repository de notifications.
    Retourne des données en mémoire pour le développement.
    """
    def list_for_user(self, user_id: int, limit: int = 10) -> List[NotificationEntity]:
        # Simule des notifications différentes selon l'utilisateur
        now = datetime.utcnow()
        
        fake_notifications = [
            NotificationEntity(
                id=1, user_id=user_id, type="stress_hydrique", title="Stress hydrique élevé",
                message=f"L'espace 'Parc Central' est en état critique.",
                level="critical", is_read=False, created_at=now - timedelta(minutes=5)
            ),
            NotificationEntity(
                id=2, user_id=user_id, type="maintenance", title="Maintenance programmée",
                message="Une maintenance du système d'arrosage est prévue demain à 10h.",
                level="info", is_read=False, created_at=now - timedelta(hours=2)
            ),
            NotificationEntity(
                id=3, user_id=user_id, type="canicule", title="Alerte canicule",
                message="Les températures dépasseront 35°C aujourd'hui. Pensez à vérifier les plantes fragiles.",
                level="warning", is_read=True, created_at=now - timedelta(days=1)
            ),
        ]
        
        if user_id == 1: # Si c'est l'admin
             fake_notifications.append(
                NotificationEntity(id=4, user_id=1, type="system", title="API Météo", message="Le service météo a répondu avec une erreur 503.", level="critical", is_read=False, created_at=now - timedelta(minutes=30))
             )

        return sorted(fake_notifications, key=lambda n: n.created_at, reverse=True)[:limit]