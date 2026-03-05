// front_end/src/components/navbar/MeteoWidget.jsx
import { useState, useEffect } from "react";
import { MapPin, Sun, WifiOff, Cloud, CloudRain, CloudDrizzle } from "lucide-react";
import { api } from "../../services/api";

const WeatherIcon = ({ condition }) => {
    const conditionStr = condition?.toLowerCase() || '';
    if (conditionStr.includes('rain')) return <CloudRain size={16} className="text-blue-400" />;
    if (conditionStr.includes('drizzle')) return <CloudDrizzle size={16} className="text-cyan-400" />;
    if (conditionStr.includes('cloud')) return <Cloud size={16} className="text-gray-400" />;
    return <Sun size={16} className="text-yellow-400" />;
};


const MeteoWidget = () => {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchWeather = (lat, lon) => {
      // NOTE: La clé API OpenWeather ne doit pas être en dur dans le code backend.
      // Elle doit être chargée depuis une variable d'environnement (ex: .env).
      api.getMeteoByCoords(lat, lon)
        .then(data => {
          setWeather(data);
          setError(null);
        })
        .catch(err => {
          console.error("Erreur API Météo:", err);
          setError("Service météo indisponible.");
        })
        .finally(() => setLoading(false));
    };

    const handleGeoSuccess = (position) => {
      const { latitude, longitude } = position.coords;
      fetchWeather(latitude, longitude);
    };

    const handleGeoError = (err) => {
      console.error("Erreur de géolocalisation:", err);
      setError("Géolocalisation refusée.");
      // Fallback: Tenter de récupérer la météo pour une ville par défaut
      // Cela évite de ne rien afficher si la géoloc est bloquée
      api.getMeteo("Lyon")
        .then(data => setWeather(data))
        .catch(() => setError("Services indisponibles."));

      setLoading(false);
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(handleGeoSuccess, handleGeoError);
    } else {
      setError("Géolocalisation non supportée.");
      setLoading(false);
    }
  }, []);

  if (loading) {
    // Shimmer effect (chargement pulsé)
    return (
      <div className="hidden sm:flex items-center gap-3 px-4 py-1.5 bg-gray-900/50 border border-gray-700 rounded-full shadow-inner animate-pulse">
        <div className="h-4 w-16 bg-gray-700 rounded"></div>
        <div className="h-3 w-12 bg-gray-700 rounded"></div>
      </div>
    );
  }

  if (error || !weather) {
    return (
       <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-red-900/50 border border-red-700 rounded-full text-red-300">
         <WifiOff size={14} />
         <span className="text-xs font-medium">{error || "Erreur"}</span>
       </div>
    );
  }

  return (
    <div className="hidden sm:flex items-center gap-3 px-4 py-1.5 bg-gray-900/50 border border-gray-700 rounded-full shadow-inner">
      <div className="flex items-center gap-2 border-r border-gray-700 pr-3">
         <WeatherIcon condition={weather.condition} />
         <span className="text-sm font-bold text-white">{Math.round(weather.temperature_c)}°C</span>
      </div>
      <div className="flex items-center gap-2">
         <MapPin size={14} className="text-gray-500" />
         <span className="text-xs text-gray-300">{weather.city}</span>
      </div>
    </div>
  );
};

export default MeteoWidget;
