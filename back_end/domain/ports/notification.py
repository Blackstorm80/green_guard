# back_end/domain/ports/notification.py
from abc import ABC, abstractmethod
from typing import List

from domain.entities.notification import NotificationEntity


class INotificationRepository(ABC):
    @abstractmethod
    def list_for_user(self, user_id: int, limit: int = 10) -> List[NotificationEntity]:
        ...