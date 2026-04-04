# back_end/infrastructure/services/meteo_open_meteo.py
import requests
from datetime import datetime
from domain.ports.meteo import IMeteoService, ConditionsMeteo


class OpenMeteoService(IMeteoService):
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def recuperer_conditions_actuelles(
        self,
        latitude: float,
        longitude: float,
        maintenant: datetime,
    ) -> ConditionsMeteo:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code,shortwave_radiation",
            "timezone": "auto",
        }

        resp = requests.get(self.BASE_URL, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        current = data["current"]

        temperature_c = current["temperature_2m"]
        weather_code = current["weather_code"]
        radiation = current.get("shortwave_radiation", 0.0)

        # règle simple d'ensoleillement fort
        ensoleillement_fort = radiation is not None and radiation > 500

        # Nom de ville : à ajuster selon l'API (Open‑Meteo ne donne pas de ville directement)
        city = data.get("timezone", "Localisation")

        condition = str(weather_code)  # ou map code -> "ensoleillé", "pluie", etc.

        return ConditionsMeteo(
            city=city,
            temperature_c=temperature_c,
            condition=condition,
            ensoleillement_fort=bool(ensoleillement_fort),
        )