from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from domain import models
from schema import utilisateurs as user_schema, notifications as notification_schema
from api.deps.auth import get_current_active_user
from infrastructure.database import get_db
from infrastructure.repositories.notification_repository_impl import NotificationRepositoryImpl
from application.use_cases.notifications import lister_notifications_user
from application.dto.user import UserDTO


router = APIRouter()


@router.get("/me", response_model=user_schema.User)
def read_current_user(
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Récupère les informations de l'utilisateur actuellement authentifié.
    """
    return current_user


@router.get("/me/notifications", response_model=List[notification_schema.NotificationRead])
def read_user_notifications(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Récupère les dernières notifications pour l'utilisateur courant.
    """
    user_dto = UserDTO(id=current_user.id, name=current_user.name, email=current_user.email, role=current_user.role)
    notif_repo = NotificationRepositoryImpl(db)
    
    # Le cas d'usage retourne des DTOs, FastAPI les mappe au `response_model`
    return lister_notifications_user(user=user_dto, notif_repo=notif_repo)