from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from infrastructure.database import get_db
from api.deps.auth import get_current_user
from domain import models
from schema.notifications import NotificationRead

router = APIRouter()

@router.get("/", response_model=List[NotificationRead])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Récupère toutes les notifications pour l'utilisateur connecté,
    les plus récentes en premier.
    """
    notifications = db.query(models.Notification)\
                      .filter(models.Notification.user_id == current_user.id)\
                      .order_by(models.Notification.cree_le.desc())\
                      .all()
    return notifications

@router.post("/{notification_id}/mark-as-read", response_model=NotificationRead)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Marque une notification spécifique comme lue.
    """
    db_notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()

    if not db_notification:
        raise HTTPException(status_code=404, detail="Notification non trouvée")

    if not db_notification.est_lue:
        db_notification.est_lue = True
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
    
    return db_notification
