from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps.auth import get_current_user
from domain import models
from infrastructure.database import get_db
from schema import notifications as notification_schema
from schema import utilisateurs as user_schema

router = APIRouter()


@router.get("/me", response_model=user_schema.User)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    """Profil de l'utilisateur authentifié."""
    return current_user


@router.get("/me/notifications", response_model=list[notification_schema.NotificationRead])
def read_user_notifications(
    limit: int = Query(10, ge=1, le=100),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dernières notifications de l'utilisateur (navbar)."""
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.cree_le.desc())
        .limit(limit)
        .all()
    )
