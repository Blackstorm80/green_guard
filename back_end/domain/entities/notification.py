# back_end/domain/entities/notification.py
from datetime import datetime

class NotificationEntity:
    def __init__(
        self,
        id: int,
        user_id: int,
        type: str,
        title: str,
        message: str,
        level: str,
        is_read: bool,
        created_at: datetime,
    ):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.title = title
        self.message = message
        self.level = level
        self.is_read = is_read
        self.created_at = created_at