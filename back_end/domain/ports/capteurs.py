# back_end/domain/ports/capteurs.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class LectureCapteur:
    def __init__(
        self,
        espace_id: int,
        temperature_c: float,
        humidite_percent: float,
        luminosite_lux: int,
        co2_ppm: int,
        o2_percent: float,
        reserve_eau_mm: float,
        timestamp: str,
    ):
        self.espace_id = espace_id
        self.temperature_c = temperature_c
        self.humidite_percent = humidite_percent
        self.luminosite_lux = luminosite_lux
        self.co2_ppm = co2_ppm
        self.o2_percent = o2_percent
        self.reserve_eau_mm = reserve_eau_mm
        self.timestamp = timestamp


class ICapteurService(ABC):
    """Port pour lire les capteurs d'un espace vert"""
    
    @abstractmethod
    def lecture_actuelle(self, espace_id: int) -> Optional[LectureCapteur]:
        """Retourne la dernière lecture des capteurs pour un espace"""
        ...
    
    @abstractmethod
    def lectures_historique(self, espace_id: int, heures: int = 24) -> list[LectureCapteur]:
        """Historique des lectures récentes"""
        ...