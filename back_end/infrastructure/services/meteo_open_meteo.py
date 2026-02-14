# back_end/infrastructure/services/meteo_open_meteo.py
import requests
from datetime import datetime
from domain.ports.meteo import IMeteoService, ConditionsMeteo


class OpenMeteoService(IMeteoService):
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def _map_weather_code_to_condition(self, code: int) -> str:
        """Traduit un code météo WMO en une condition textuelle simple."""
        # Source: Documentation Open-Meteo sur les codes WMO
        if code == 0:
            return "Ciel clair"
        if code in [1, 2, 3]:
            return "Partiellement nuageux"
        if code in [45, 48]:
            return "Brouillard"
        if code in [51, 53, 55, 56, 57]:
            return "Bruine"
        if code in [61, 63, 65, 66, 67]:
            return "Pluie"
        if code in [71, 73, 75, 77]:
            return "Neige"
        if code in [80, 81, 82]:
            return "Averses de pluie"
        if code in [85, 86]:
            return "Averses de neige"
        if code in [95, 96, 99]:
            return "Orage"
        return f"Code {code}"

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

        # règle simple : ensoleillement fort si radiation > 500 W/m²
        ensoleillement_fort = radiation is not None and radiation > 500

        # Nom de ville : à ajuster selon l'API (Open‑Meteo ne donne pas de ville directement)
        city = data.get("timezone", "Localisation")

        condition = self._map_weather_code_to_condition(weather_code)

        return ConditionsMeteo(
            city=city,
            temperature_c=temperature_c,
            condition=condition,
            ensoleillement_fort=bool(ensoleillement_fort),
        )
