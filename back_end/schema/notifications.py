from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    message: str
    type: str

class NotificationRead(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
