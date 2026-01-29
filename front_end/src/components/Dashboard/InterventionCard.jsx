// components/Dashboard/InterventionCard.jsx
function InterventionCard({ data }) {
  const {
    title,
    label,
    desc,
    priority = "high",
    status = "pending",
    timestamp,
    location,
    onClick
  } = data;

  // ========== سیستم تشخیص خودکار اولویت ==========
  const detectPriority = () => {
    const titleLower = title.toLowerCase();
    const labelLower = label?.toLowerCase() || "";
    const descLower = desc.toLowerCase();

    const criticalKeywords = [
      'mortalité', 'mortality', 'mort', 'dead', 'perte totale',
      'critique', 'critical', 'urgence', 'emergency',
      'arrêt', 'stop', 'down', 'hors service', 'offline',
      'catastrophe', 'catastrophic', 'disaster'
    ];

    const highKeywords = [
      'sec', 'dry', 'arid', 'drought',
      'chaleur', 'heat', 'hot', 'température',
      'pression', 'pressure', 'stress',
      'alerte', 'alert', 'warning',
      'massive', 'massif', 'important'
    ];

    const mediumKeywords = [
      'surveillance', 'monitoring', 'observation',
      'léger', 'light', 'mineur', 'minor',
      'attention', 'attention needed',
      'baisse', 'drop', 'decrease'
    ];

    const checkText = (text) => {
      return {
        isCritical: criticalKeywords.some(keyword => text.includes(keyword)),
        isHigh: highKeywords.some(keyword => text.includes(keyword)),
        isMedium: mediumKeywords.some(keyword => text.includes(keyword))
      };
    };

    const titleCheck = checkText(titleLower);
    const labelCheck = checkText(labelLower);
    const descCheck = checkText(descLower);

    if (titleCheck.isCritical || labelCheck.isCritical || descCheck.isCritical) {
      return "critical";
    }
    if (titleCheck.isHigh || labelCheck.isHigh || descCheck.isHigh) {
      return "high";
    }
    if (titleCheck.isMedium || labelCheck.isMedium || descCheck.isMedium) {
      return "medium";
    }

    return "high";
  };

  // ========== تشخیص خودکار وضعیت ==========
  const detectStatus = () => {
    if (status && status !== "pending") return status;
    
    const descLower = desc.toLowerCase();
    
    if (descLower.includes('résolu') || descLower.includes('solved') || 
        descLower.includes('terminé') || descLower.includes('finished')) {
      return "resolved";
    }
    
    if (descLower.includes('en cours') || descLower.includes('in progress') ||
        descLower.includes('intervention') || descLower.includes('travail')) {
      return "in-progress";
    }
    
    return "pending";
  };

  // ========== تشخیص خودکار رنگ و استایل ==========
  const getConfig = () => {
    const detectedPriority = priority === "auto" ? detectPriority() : priority;
    const detectedStatus = detectStatus();

    const priorityConfigs = {
      critical: {
        border: "border-red-500",
        borderGlow: "shadow-[0_0_15px_rgba(239,68,68,0.3)]",
        badge: "bg-red-500",
        label: "Critique",
        icon: "🔥",
        bg: "bg-gradient-to-r from-red-500/5 to-transparent",
        pulse: "animate-pulse"
      },
      high: {
        border: "border-orange-500",
        borderGlow: "shadow-[0_0_12px_rgba(249,115,22,0.25)]",
        badge: "bg-orange-500",
        label: "Haute",
        icon: "⚡",
        bg: "bg-gradient-to-r from-orange-500/5 to-transparent",
        pulse: ""
      },
      medium: {
        border: "border-yellow-500",
        borderGlow: "shadow-[0_0_10px_rgba(245,158,11,0.2)]",
        badge: "bg-yellow-500",
        label: "Moyenne",
        icon: "⚠️",
        bg: "bg-gradient-to-r from-yellow-500/5 to-transparent",
        pulse: ""
      }
    };

    const statusConfigs = {
      pending: {
        statusIcon: "⏳",
        statusText: "En attente",
        statusColor: "text-red-400",
        statusAnimation: "animate-[pulse_2s_ease-in-out_infinite]"
      },
      "in-progress": {
        statusIcon: "🔄",
        statusText: "En cours",
        statusColor: "text-blue-400",
        statusAnimation: "animate-[spin_3s_linear_infinite]"
      },
      resolved: {
        statusIcon: "✅",
        statusText: "Résolu",
        statusColor: "text-green-400",
        statusAnimation: ""
      }
    };

    const priorityConfig = priorityConfigs[detectedPriority] || priorityConfigs.high;
    const statusConfig = statusConfigs[detectedStatus] || statusConfigs.pending;

    return {
      priority: detectedPriority,
      status: detectedStatus,
      priorityConfig,
      statusConfig
    };
  };

  // ========== تشخیص خودکار موقعیت ==========
  const detectLocation = () => {
    if (location) return location;
    
    const locationKeywords = [
      'bibliothèque', 'library', 'mairie', 'town hall', 
      'jardin', 'garden', 'zac', 'zone', 'toit', 'roof',
      'mur', 'wall', 'salle', 'room', 'bâtiment', 'building'
    ];
    
    for (const keyword of locationKeywords) {
      if (title.toLowerCase().includes(keyword)) {
        return title;
      }
    }
    
    return "Non spécifié";
  };

  // ========== محاسبه زمان ==========
  const getTimeAgo = () => {
    if (timestamp) return timestamp;
    
    const config = getConfig();
    switch (config.priority) {
      case "critical": return "À l'instant";
      case "high": return "Il y a 15min";
      default: return "Il y a 30min";
    }
  };

  const config = getConfig();
  const detectedLocation = detectLocation();
  const timeAgo = getTimeAgo();

  return (
  <div
    className={`
      bg-gray-900 p-4 rounded-xl border-l-4 ${config.priorityConfig.border} 
      transition-all duration-600 cursor-pointer group
      ${config.priorityConfig.bg}
      hover:${config.priorityConfig.borderGlow}
      hover:shadow-lg
      relative
      overflow-hidden
      before:absolute before:inset-0 
      before:bg-gradient-to-r before:from-transparent before:via-white/5 before:to-transparent
      before:translate-x-[-100%]
      hover:before:translate-x-[100%]
      before:transition-transform before:duration-900
      before:ease-out
    `}
    onClick={onClick}
    role="button"
    tabIndex={0}
    style={{ willChange: 'transform, box-shadow' }}
  >
    {/* خط متحرک حاشیه چپ */}
    <div className={`
      absolute left-0 top-0 bottom-0 w-1
      ${config.priorityConfig.border.replace('border-', 'bg-')}
      opacity-50
      group-hover:opacity-100
      group-hover:animate-[pulse_2.1s_ease-in-out_infinite]
      transition-opacity duration-600
    `}></div>

    {/* هدر کارت */}
    <div className="flex justify-between items-start mb-3 relative z-10">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-lg ${config.priorityConfig.pulse}`}>
            {config.priorityConfig.icon}
          </span>
          <h4 className="text-white font-bold text-sm truncate group-hover:text-white/90 transition-colors duration-600">
            {title}
          </h4>
        </div>
        
        <div className="flex items-center gap-2 text-xs text-slate-400 group-hover:text-slate-300 transition-colors duration-600">
          <span className="flex items-center gap-1">
            <span className="text-[10px]">📍</span>
            <span>{detectedLocation}</span>
          </span>
          <span className="w-1 h-1 bg-gray-600 rounded-full group-hover:bg-gray-500 transition-colors duration-600"></span>
          <span>{timeAgo}</span>
        </div>
      </div>
      
      <div className="flex flex-col items-end gap-1">
        <span className={`
          ${config.priorityConfig.badge} text-white px-2 py-1 rounded text-[10px] font-bold
          group-hover:shadow-md
          transition-all duration-600
        `}>
          {label || config.priorityConfig.label}
        </span>
        
        <span className={`
          ${config.statusConfig.statusColor} text-[9px] font-medium flex items-center gap-1
          ${config.statusConfig.statusAnimation}
          transition-all duration-600
        `}>
          {config.statusConfig.statusIcon} {config.statusConfig.statusText}
        </span>
      </div>
    </div>

    {/* توضیحات */}
    <p className="text-xs text-slate-300 mt-2 line-clamp-2 group-hover:text-slate-200 transition-colors duration-600 relative z-10">
      {desc}
    </p>

    {/* اطلاعات اضافی (با انیمیشن ارتفاع نرم) */}
    <div className={`
      max-h-0 overflow-hidden
      group-hover:max-h-20
      transition-all duration-100 ease-in-out
      opacity-0 group-hover:opacity-100
      delay-300
    `}>
      <div className="
        flex justify-between items-center 
        mt-3 pt-3 border-t border-gray-800/50 
        text-[10px] text-slate-500 group-hover:text-slate-400
        animate-[slideInLeft_0.3s_ease-out]
      ">
        <div className="flex items-center gap-1">
          <span className="w-1.5 h-1.5 bg-gray-500 rounded-full group-hover:bg-gray-400 transition-colors duration-600"></span>
          <span>Priorité: {config.priority}</span>
        </div>
        
        <button 
          className="
            text-slate-400 hover:text-white px-2 py-0.5 rounded border border-gray-700 
            hover:border-gray-600 transition-all duration-600
            hover:shadow-sm
            hover:bg-gray-800/50
            animate-[slideInRight_0.3s_ease-out]
          "
          onClick={(e) => {
            e.stopPropagation();
            console.log(`Agir sur: ${title}`);
          }}
        >
          Agir →
        </button>
      </div>
    </div>

    {/* افکت نور پس‌زمینه */}
    <div className={`
      absolute inset-0 rounded-xl
      bg-gradient-to-r from-transparent via-white/[0.02] to-transparent
      opacity-0 group-hover:opacity-100
      transition-opacity duration-600
      pointer-events-none
    `}></div>
  </div>
);
}

export default InterventionCard;