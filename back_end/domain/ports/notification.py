# back_end/domain/ports/notification.py
from abc import ABC, abstractmethod
from typing import List

from domain.models import Notification

class INotificationRepository(ABC):
    @abstractmethod
    def list_for_user(self, user_id: int, limit: int = 10) -> List[Notification]:
        ...