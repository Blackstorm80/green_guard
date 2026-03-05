
function ZoneCard({ data }) {
  const {
    title,
    spacesCount,
    status = "normal", // "normal", "stress", "excellent", "warning"
    okCount = 0,
    warningCount = 0,
    criticalCount = 0,
    subtitle,
    customColors,
    onClick,
    className = ""
  } = data;

  const statusConfig = {
    stress: {
      border: "border-red-500/40 hover:border-red-500",
      badge: "bg-red-500/20 text-red-400",
      badgeText: "Stress",
      colors: customColors || ["green", "yellow", "red"]
    },
    excellent: {
      border: "border-gray-700 hover:border-green-500",
      badge: "bg-green-500/20 text-green-400",
      badgeText: "Excellent",
      colors: customColors || ["green", "yellow", "gray"]
    },
    warning: {
      border: "border-yellow-500/40 hover:border-yellow-500",
      badge: "bg-yellow-500/20 text-yellow-400",
      badgeText: "Warning",
      colors: customColors || ["green", "yellow", "orange"]
    },
    normal: {
      border: "border-gray-700 hover:border-blue-500",
      badge: "bg-blue-500/20 text-blue-400",
      badgeText: "Normal",
      colors: customColors || ["green", "yellow", "gray"]
    }
  };

  const config = statusConfig[status] || statusConfig.normal;
  
  const total = okCount + warningCount + criticalCount;
  const percentages = {
    ok: total > 0 ? (okCount / total) * 100 : 0,
    warning: total > 0 ? (warningCount / total) * 100 : 0,
    critical: total > 0 ? (criticalCount / total) * 100 : 0
  };

  const colorMap = {
    green: "bg-green-500",
    yellow: "bg-yellow-500",
    red: "bg-red-500",
    orange: "bg-orange-500",
    gray: "bg-gray-500",
    blue: "bg-blue-500"
  };

  return (
    <div 
      className={`bg-gray-800 p-5 rounded-2xl border ${config.border} transition-all cursor-pointer shadow-lg hover:shadow-xl ${className}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="text-white font-bold text-lg">{title}</h4>
          <p className="text-xs text-slate-400">
            {spacesCount} Espace{spacesCount !== 1 ? 's' : ''}
          </p>
        </div>
        <span className={`${config.badge} px-2 py-1 rounded text-xs font-bold`}>
          {config.badgeText}
        </span>
      </div>

      <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden flex mb-2">
        {percentages.ok > 0 && (
          <div 
            className={`h-full transition-all duration-500 ${colorMap[config.colors[0]]}`}
            style={{ width: `${percentages.ok}%` }}
          />
        )}
        {percentages.warning > 0 && (
          <div 
            className={`h-full transition-all duration-500 ${colorMap[config.colors[1]]}`}
            style={{ width: `${percentages.warning}%` }}
          />
        )}
        {percentages.critical > 0 && (
          <div 
            className={`h-full transition-all duration-500 ${colorMap[config.colors[2]]} ${status === 'stress' ? 'animate-pulse' : ''}`}
            style={{ width: `${percentages.critical}%` }}
          />
        )}
      </div>

      <div className="flex flex-wrap justify-between items-center gap-2 text-xs">
        <div className="flex flex-wrap gap-3">
          {okCount > 0 && (
            <span className="text-green-400 flex items-center gap-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              {okCount} OK
            </span>
          )}
          {warningCount > 0 && (
            <span className="text-yellow-400 flex items-center gap-1">
              <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
              {warningCount} Warning
            </span>
          )}
        </div>
        <div>
          {criticalCount > 0 ? (
            <span className="text-red-400 font-bold flex items-center gap-1">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              {criticalCount} Critique{criticalCount > 1 ? 's' : ''}
            </span>
          ) : (
            <span className="text-slate-500">0 Critique</span>
          )}
        </div>
      </div>

      {subtitle && (
        <p className="text-xs text-slate-500 mt-3 pt-3 border-t border-gray-700">
          {subtitle}
        </p>
      )}
    </div>
  );
}

export default ZoneCard;