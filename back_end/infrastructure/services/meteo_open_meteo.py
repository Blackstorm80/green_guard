import python_weather
import asyncio
from sqlalchemy.orm import Session
from domain.models import EspaceVert
from infrastructure.database import SessionLocal
from domain.ports.meteo import IMeteoService, ConditionsMeteo
from datetime import datetime

class OpenMeteoService(IMeteoService):
    
    async def _get_weather_async(self, latitude: float, longitude: float):
        async with python_weather.Client(unit=python_weather.METRIC) as client:
            return await client.get(f"{latitude},{longitude}")

    def recuperer_conditions_actuelles(
        self,
        latitude: float,
        longitude: float,
        maintenant: datetime,
    ) -> ConditionsMeteo:
        try:
            weather = asyncio.run(self._get_weather_async(latitude, longitude))
            
            # Déduction de l'ensoleillement fort à partir des conditions actuelles
            sunny_conditions = ["sunny", "clear"]
            ensoleillement_fort = any(cond in weather.description.lower() for cond in sunny_conditions)

            # python-weather ne fournit pas nativement et0
            et0_estime = None

            return ConditionsMeteo(
                city="Inconnu", # python-weather ne fournit pas de nom de ville pour les coordonnées
                temperature_c=weather.temperature,
                condition=weather.description,
                ensoleillement_fort=ensoleillement_fort,
                humidite=weather.humidity,
                pluie=weather.precipitation,
                et0=et0_estime
            )
        except Exception as e:
            import logging
            logging.error(f"Erreur lors de la récupération de la météo avec python-weather: {e}")
            return None

    def recuperer_meteo_pour_tous_les_espaces(self):
        db: Session = SessionLocal()
        try:
            espaces = db.query(EspaceVert).all()
            all_weather_data = []

            for espace in espaces:
                weather_data = self.recuperer_conditions_actuelles(espace.latitude, espace.longitude, datetime.utcnow())
                if not weather_data:
                    continue
                # Ici on pourrait stocker les données ou les retourner
                all_weather_data.append({
                    "espace_id": espace.id,
                    "nom": espace.nom,
                    "weather": {
                        "temperature": weather_data.temperature_c,
                        "condition": weather_data.condition,
                        "ensoleillement_fort": weather_data.ensoleillement_fort,
                        "humidite": weather_data.humidite,
                        "pluie": weather_data.pluie
                    }
                })
            return all_weather_data
        finally:
            db.close()
