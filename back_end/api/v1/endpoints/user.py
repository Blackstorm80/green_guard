# back_end/api/v1/endpoints/user.py
from typing import List
from fastapi import APIRouter, Depends

from application.dto.notification import NotificationDTO
from application.dto.user import UserDTO
from application.use_cases.notifications import lister_notifications_user
from api.deps.auth import get_current_user
from infrastructure.repositories.notification_repository_impl import NotificationRepositoryImpl
from domain.ports.notification import INotificationRepository

router = APIRouter(prefix="/user", tags=["User"])


def get_notification_repo() -> INotificationRepository:
    # Pour l'instant, on retourne une implémentation "fake" en mémoire.
    # Plus tard, on injectera la session de base de données ici.
    return NotificationRepositoryImpl()


@router.get("/notifications", response_model=List[NotificationDTO])
async def get_user_notifications(
    current_user: UserDTO = Depends(get_current_user),
    notif_repo: INotificationRepository = Depends(get_notification_repo),
    limit: int = 10,
):
    return lister_notifications_user(
        user=current_user,
        notif_repo=notif_repo,
        limit=limit,
    )