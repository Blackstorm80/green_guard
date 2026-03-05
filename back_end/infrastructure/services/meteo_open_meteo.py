import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Import des ports du domaine (L'oignon)
from domain.ports.meteo import IMeteoService, ConditionsMeteo

load_dotenv()

class OpenMeteoService(IMeteoService):
    """
    Note : On garde le nom 'OpenMeteoService' pour la compatibilité des imports,
    mais on utilise l'API OpenWeatherMap à l'intérieur.
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def _map_owm_to_condition(self, code: int) -> str:
        """Traduit les codes OpenWeatherMap en texte lisible."""
        if 200 <= code <= 232: return "Orage"
        if 300 <= code <= 321: return "Bruine"
        if 500 <= code <= 531: return "Pluie"
        if 600 <= code <= 622: return "Neige"
        if code == 800: return "Ciel clair"
        if 801 <= code <= 804: return "Nuageux"
        return "Conditions variables"

    def recuperer_conditions_actuelles(
        self,
        latitude: float,
        longitude: float,
        maintenant: datetime,
    ) -> ConditionsMeteo:
        
        # Récupération de la clé API
        api_key = os.getenv("OPENWEATHER_API_KEY")
        
        if not api_key:
            raise ValueError("La clé OPENWEATHER_API_KEY est manquante dans le fichier .env")

        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": api_key,
            "units": "metric",
            "lang": "fr"
        }

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=5)
            
            if resp.status_code == 401:
                print(" Erreur 401 : Clé API invalide ou non activée (attendre 1h si nouvelle).")
                
            resp.raise_for_status()
            data = resp.json()

            # Extraction des données réelles
            temperature_c = data["main"]["temp"]
            weather_code = data["weather"][0]["id"]
            city = data.get("name", "Localisation")
            
            # Déduction de l'ensoleillement
            ensoleillement_fort = weather_code == 800 or weather_code == 801

            return ConditionsMeteo(
                city=city,
                temperature_c=temperature_c,
                condition=self._map_owm_to_condition(weather_code),
                ensoleillement_fort=ensoleillement_fort,
            )

        except Exception as e:
            print(f"Erreur lors de l'appel météo : {e}")
            # Retourne une valeur par défaut pour ne pas faire crasher tout le dashboard
            return ConditionsMeteo(
                city="Erreur Météo",
                temperature_c=0.0,
                condition="Indisponible",
                ensoleillement_fort=False
            )