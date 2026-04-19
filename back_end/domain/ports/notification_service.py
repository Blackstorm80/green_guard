# Fichier : domain/ports/notification_service.py

from abc import ABC, abstractmethod


class INotificationService(ABC):
    """
    Interface (Port) pour un service d'envoi de notifications.
    """

    @abstractmethod
    def notifier_stress_hydrique(self, nom_espace: str, statut: str, indice_stress: float) -> None:
        """
        Envoie une notification concernant le statut de stress hydrique d'un espace.
        log au debut  (rajout de email et sms a la prochane version)
        """
        pass