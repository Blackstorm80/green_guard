# back_end/application/use_cases/notifications.py
from typing import List

from application.dto.notification import NotificationDTO
from domain.ports.notification import INotificationRepository
from application.dto.user import UserDTO


def lister_notifications_user(
    user: UserDTO,
    notif_repo: INotificationRepository,
    limit: int = 10,
) -> List[NotificationDTO]:
    """
    Récupère les dernières notifications d'un utilisateur pour la Navbar.
    """
    notifications = notif_repo.list_for_user(user.id, limit=limit)
    return [
        NotificationDTO(
            id=n.id,
            type=n.type,
            title=n.title,
            message=n.message,
            level=n.level,
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in notifications
    ]