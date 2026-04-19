import requests
import logging
from datetime import datetime

import python_weather
import asyncio
from sqlalchemy.orm import Session
from domain.models import EspaceVert
from infrastructure.database import SessionLocal
from domain.ports.meteo import IMeteoService, ConditionsMeteo

class OpenMeteoService(IMeteoService):
    def recuperer_conditions_actuelles(self, latitude, longitude, maintenant) -> ConditionsMeteo:
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,precipitation,cloud_cover&daily=et0_fao_evapotranspiration&timezone=auto"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current", {})
            daily = data.get("daily", {})

            # Déduction de l'ensoleillement : couverture nuageuse < 30%
            cloud_cover = current.get("cloud_cover", 100)
            ensoleillement_fort = cloud_cover < 30
            
            # Récupération de l'ET0 (évapotranspiration) réelle
            et0_list = daily.get("et0_fao_evapotranspiration", [])
            et0_reelle = et0_list[0] if et0_list else None

            return ConditionsMeteo(
                city="Ma Station",
                temperature_c=current.get("temperature_2m"),
                condition="Dégagé" if ensoleillement_fort else "Nuageux",
                ensoleillement_fort=ensoleillement_fort,
                humidite=current.get("relative_humidity_2m"),
                pluie=current.get("precipitation", 0.0),
                et0=et0_reelle
            )
        except Exception as e:
            logging.error(f"ERREUR CRITIQUE OPEN-METEO : {e}")
            return None