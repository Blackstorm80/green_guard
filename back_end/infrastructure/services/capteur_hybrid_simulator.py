# back_end/infrastructure/services/capteur_hybrid_simulator.py
from datetime import datetime
import random
from typing import Dict, Any, Optional, List

from domain.ports.meteo import ConditionsMeteo
from domain.ports.capteurs import ICapteurService, LectureCapteur


class CapteurHybridSimulator(ICapteurService):
    def __init__(self):
        self.lectures_historique_cache: Dict[int, List[Dict]] = {}
        self.temperature_exterieure_base = 10.0  # Lyon février
        
    def lecture_actuelle(self, espace_id: int) -> Optional[LectureCapteur]:
        # Simule en combinant météo + spécificités locales
        meteo_simulee = self._simuler_meteo_exterieure()
        lecture_brute = self._simuler_lecture_locale(espace_id, meteo_simulee)
        
        # Stocke pour historique
        if espace_id not in self.lectures_historique_cache:
            self.lectures_historique_cache[espace_id] = []
        self.lectures_historique_cache[espace_id].append(lecture_brute)
        if len(self.lectures_historique_cache[espace_id]) > 100:
            self.lectures_historique_cache[espace_id] = self.lectures_historique_cache[espace_id][-100:]
        
        return LectureCapteur(**lecture_brute)
    
    def _simuler_meteo_exterieure(self) -> ConditionsMeteo:
        """Simule météo réaliste Lyon (février)"""
        return ConditionsMeteo(
            city="Lyon",
            temperature_c=round(10.0 + random.uniform(-3, 2), 1),
            condition="nuageux",
            ensoleillement_fort=False
        )
    
    def _simuler_lecture_locale(self, espace_id: int, meteo: ConditionsMeteo) -> Dict[str, Any]:
        # Température (effet isolation)
        isolation = 0.7 if espace_id % 2 == 0 else 0.4
        temp_locale = meteo.temperature_c * (1-isolation) + 18*isolation + random.uniform(-1,1)
        
        # Humidité
        humidite = min(95, max(25, 60 + random.uniform(-10,10)))
        
        # Luminosité (faible en février)
        luminosite = max(20, 150 * (0.3 + random.uniform(-0.1,0.2)))
        
        # CO2 (réaliste 400-2000ppm)
        co2 = self._calculer_co2(espace_id, temp_locale, humidite, luminosite)
        
        # O2 (20.5-21.0%)
        o2 = self._calculer_o2(co2, espace_id)
        
        # Réserve eau
        reserve_eau = max(0, min(100, 65 + random.uniform(-25,15)))
        
        return {
            "espace_id": espace_id,
            "temperature_c": round(temp_locale, 1),
            "humidite_percent": round(humidite, 1),
            "luminosite_lux": int(luminosite),
            "co2_ppm": int(co2),
            "o2_percent": round(o2, 2),
            "reserve_eau_mm": round(reserve_eau, 1),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculer_co2(self, espace_id: int, temp: float, humidite: float, lumi: int) -> float:
        base_co2 = 450
        if espace_id % 3 == 0: base_co2 += random.uniform(400, 1000)
        if lumi > 150: base_co2 -= min(120, lumi / 8)
        base_co2 += (temp - 15) * 18
        return max(350, min(2500, base_co2 + random.uniform(-40, 40)))
    
    def _calculer_o2(self, co2_ppm: float, espace_id: int) -> float:
        base_o2 = 20.95
        photosynthese = 0.12 if espace_id % 2 == 1 else 0.06
        o2_reduction = max(0, (co2_ppm - 450) / 6000 * 0.35)
        return max(19.2, min(21.2, base_o2 + photosynthese - o2_reduction))
    
    def lectures_historique(self, espace_id: int, heures: int = 24) -> List[LectureCapteur]:
        hist = self.lectures_historique_cache.get(espace_id, [])
        # Simule un historique court pour l'exemple
        return [LectureCapteur(**l) for l in hist[-12:]]