import { useState, useEffect } from "react";
import AlertsPanel from "../../components/Alerts/AlertsPanel";

function Alertes() {
  const [alertsData, setAlertsData] = useState([]);
  const [spacesData, setSpacesData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
   
        
        const mockAlerts = [
          {
            title: "Stress Hydrique",
            count: 12,
            description: "Zone Nord • Impact critique",
            colorBorder: "border-red-400/40",
            colorBg: "bg-red-400/10",
            colorBadgeBg: "bg-red-500/20",
            colorText: "text-red-400"
          },
          {
            title: "Canicule",
            count: 4,
            description: "Tous secteurs • Surveillance",
            colorBorder: "border-amber-400/40",
            colorBg: "bg-amber-400/10",
            colorBadgeBg: "bg-amber-400/20",
            colorText: "text-amber-400"
          }
        ];

        const mockSpaces = [
          { name: "Toit Bibliothèque Centrale" },
          { name: "Jardin ZAC Nord" },
          { name: "Parc des Expositions" }
        ];

        setAlertsData(mockAlerts);
        setSpacesData(mockSpaces);
        setLoading(false);
      } catch (error) {
        console.error("Erreur lors du chargement:", error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div className="text-white p-10">Chargement...</div>;

  return (
    <div className="p-8">
      <AlertsPanel 
        alerts={alertsData} 
        impactedSpaces={spacesData} 
      />
    </div>
  );
}

export default Alertes;