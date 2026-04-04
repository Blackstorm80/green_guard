# back_end/application/dto/notification.py
from pydantic import BaseModel
from datetime import datetime


class NotificationDTO(BaseModel):
    id: int
    type: str          # "stress_hydrique", "canicule", "maintenance", ...
    title: str
    message: str
    level: str         # "info", "warning", "critical"
    is_read: bool
    created_at: datetime