function StatCard({ data }) {
  const {
    title,
    value,
    unit,
    subtitle = "",
    color = "text-white",
    alert = false,
    alertText = "",
    alertIcon = "🚨",
    showIcon = true,
    customBorder = "",
    customBg = "",
    priority = "normal",
  } = data;

  const analyzeMetric = () => {
    const titleLower = title.toLowerCase();
    const subtitleLower = subtitle.toLowerCase();

    const higherIsBetterKeywords = [
      "santé",
      "health",
      "qualité",
      "performance",
      "efficacité",
      "score",
      "satisfaction",
      "disponibilité",
      "batterie",
      "charge",
      "stockage",
      "couverture",
      "bon",
      "excellent",
      "succès",
      "gain",
      "croissance",
      "rendement",
      "production",
      "vitesse",
      "séquestré",
      "positive",
      "floraison",
      "récolte",
      "biomasse",
      "biodiversité",
      "uptime",
      "disponibility",
      "availability",
      "réussite",
      "success",
      "profit",
      "revenue",
      "income",
      "sécurité",
      "security",
      "protection",
      "safety",
    ];

    const lowerIsBetterKeywords = [
      "erreur",
      "error",
      "échec",
      "fail",
      "failure",
      "bug",
      "défaillance",
      "consommation",
      "consumption",
      "coût",
      "cost",
      "dépense",
      "expense",
      "gaspillage",
      "waste",
      "perte",
      "loss",
      "downtime",
      "stress",
      "risque",
      "risk",
      "alerte",
      "alert",
      "critique",
      "critical",
      "surcharge",
      "overload",
      "température",
      "temperature",
      "chaleur",
      "heat",
      "humidité",
      "humidity",
      "pression",
      "pressure",
      "bruit",
      "noise",
      "pollution",
      "poussière",
      "dust",
      "latence",
      "latency",
      "délai",
      "delay",
      "panne",
      "breakdown",
      "corruption",
      "vulnérabilité",
      "vulnerability",
      "menace",
      "threat",
      "négatif",
      "negative",
      "danger",
      "dangerous",
      "taux d'erreur",
      "error rate",
      "temps d'arrêt",
      "downtime",
      "fuite",
      "leak",
      "incident",
      "accident",
      "problème",
      "problem",
      "déchet",
      "waste",
      "émission",
      "emission",
      "toxique",
      "toxic",
    ];

    const isHigherBetter = higherIsBetterKeywords.some((w) =>
      titleLower.includes(w)
    );
    const isLowerBetter = lowerIsBetterKeywords.some((w) =>
      titleLower.includes(w)
    );

    let higherIsBetter = true; 
    if (isLowerBetter) higherIsBetter = false;

    let trendIcon = "➡";
    let trendColor = "text-gray-400";
    let label = "Stable";

    const changeMatch = subtitle.match(/[+-]?\d+(\.\d+)?/);
    if (changeMatch) {
      const change = parseFloat(changeMatch[0]);
      const isIncrease = change > 0;
      const isDecrease = change < 0;

      if (isIncrease) {
        trendIcon = "▲";
        if (higherIsBetter) {
          trendColor = "text-green-400";
          label = "Amélioration";
        } else {
          trendColor = "text-red-400";
          label = "Dégradation";
        }
      } else if (isDecrease) {
        trendIcon = "▼";
        if (higherIsBetter) {
          trendColor = "text-red-400";
          label = "Dégradation";
        } else {
          trendColor = "text-green-400";
          label = "Amélioration";
        }
      }
    } else {
      if (
        subtitleLower.includes("stable") ||
        subtitleLower.includes("normal") ||
        subtitleLower.includes("constant")
      ) {
        trendIcon = "➡";
        trendColor = "text-gray-400";
        label = "Stable";
      }
    }

    if (
      subtitleLower.includes("amélioration") ||
      subtitleLower.includes("improvement") ||
      subtitleLower.includes("better") ||
      subtitleLower.includes("bon")
    ) {
      trendColor = "text-green-400";
      label = "Amélioration";
    } else if (
      subtitleLower.includes("dégradation") ||
      subtitleLower.includes("worse") ||
      subtitleLower.includes("deterioration")
    ) {
      trendColor = "text-red-400";
      label = "Dégradation";
    }

    return {
      icon: trendIcon,
      colorClass: trendColor,
      ringClass:
        trendColor === "text-green-400"
          ? "ring-1 ring-green-500"
          : trendColor === "text-red-400"
          ? "ring-1 ring-red-500"
          : "ring-1 ring-gray-600",
      bgClass:
        trendColor === "text-green-400"
          ? "bg-green-500/10"
          : trendColor === "text-red-400"
          ? "bg-red-500/10"
          : "bg-gray-500/10",
      label: label,
      higherIsBetter: higherIsBetter,
    };
  };

  const isAlertCard = () => {
    const titleLower = title.toLowerCase();
    const hasAlert =
      titleLower.includes("stress") ||
      titleLower.includes("critique") ||
      titleLower.includes("danger") ||
      subtitle.includes("Action immédiate") ||
      subtitle.includes("urgence");

    return alert || hasAlert;
  };

  const alertMode = isAlertCard();
  const analysis = analyzeMetric();

 
if (alertMode) {
  return (
    <div className={` p-4 md:p-5 rounded-xl md:rounded-2xl shadow-lg relative overflow-hidden ${customBg}`}>
      <p className="text-slate-400 text-[10px] xs:text-xs uppercase font-bold tracking-wider text-red-500 truncate">
        {title}
      </p>
      
      <div className="flex items-center justify-between mt-1 md:mt-2">
        <div className="min-w-0 flex-1">
          <h3 className="text-2xl md:text-3xl font-bold text-red-500 truncate">
            {value}
            {unit && <span className="text-sm md:text-lg text-slate-500 ml-1">{unit}</span>}
          </h3>
          <p className="text-[10px] md:text-xs text-red-300 mt-1 truncate">
            {alertText || subtitle || "Attention requise"}
          </p>
        </div>
        
        <div className="text-red-500 text-2xl md:text-4xl ml-2 md:ml-4 flex-shrink-0">
          {alertIcon}
        </div>
      </div>
    </div>
  );
}

  return (
    <div
      className={`bg-gray-800 p-4 md:p-5 rounded-xl md:rounded-2xl shadow-lg hover:ring-1 hover:ring-gray-600 transition-all duration-200 ${customBg}`}
    >
      <p className="text-slate-400 text-[10px] xs:text-xs uppercase font-bold tracking-wider truncate">
        {title}
      </p>

      <div className="flex items-center justify-between mt-2 md:mt-3">
        <div className="min-w-0 flex-1">
          <h3 className={`text-2xl md:text-3xl font-bold ${color} truncate`}>
            {value}
            {unit && (
              <span className="text-sm md:text-lg text-slate-500 ml-1">
                {unit}
              </span>
            )}
          </h3>
        </div>

        {showIcon && (
          <div className="flex flex-col items-center ml-2 md:ml-4 flex-shrink-0">
            <span className={`text-2xl md:text-4xl ${analysis.colorClass}`}>
              {analysis.icon}
            </span>
            <span
              className={`hidden xs:block text-[10px] md:text-xs mt-1 ${analysis.colorClass} font-semibold truncate`}
            >
              {analysis.label}
            </span>
          </div>
        )}
      </div>

      {subtitle && (
        <div
          className={`mt-2 md:mt-3 text-[10px] md:text-xs px-2 md:px-3 py-1 md:py-2 rounded-lg ${analysis.bgClass} inline-block max-w-full`}
        >
          <span
            className={`${analysis.colorClass} truncate inline-block max-w-full`}
          >
            {subtitle}
          </span>
        </div>
      )}
    </div>
  );
}
export default StatCard;
