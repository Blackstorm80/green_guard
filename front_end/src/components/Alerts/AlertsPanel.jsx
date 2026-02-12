function AlertsPanel({ alerts, impactedSpaces }) {
  return (
    <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6 shadow-lg">
      {/* HEADER */}
      <div className="border-b border-slate-600 pb-4 mb-4">
        <h3 className="text-lg font-bold text-white">
          Gestion des alertes écologiques
        </h3>
        <p className="text-xs text-slate-400">
          Vue groupée par typologie
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ALERT TYPES */}
        <div className="space-y-4">
          {alerts.map((alert, index) => (
            <div 
              key={index}
              className={`border ${alert.colorBorder} ${alert.colorBg} rounded-xl hover:opacity-80 transition cursor-pointer`}
            >
              <div className="p-4 flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg ${alert.colorBadgeBg} ${alert.colorText} flex items-center justify-center font-bold`}>
                    {alert.count}
                  </div>
                  <div>
                    <h4 className={`font-bold ${alert.colorText}`}>
                      {alert.title}
                    </h4>
                    <p className="text-xs text-slate-300">
                      {alert.description}
                    </p>
                  </div>
                </div>
                <span className="text-slate-400 hover:text-white">
                  Détails →
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* IMPACTED SPACES */}
        <div className="bg-slate-900/40 border border-slate-600 rounded-xl p-4">
          <h4 className="text-sm font-bold text-white mb-3">
            Espaces impactés
          </h4>
          <ul className="space-y-2 text-slate-300 text-sm">
            {impactedSpaces.map((space, index) => (
              <li key={index} className="flex justify-between items-center bg-slate-800 p-2 rounded">
                <span>• {space.name}</span>
                <button className="text-green-400 text-xs border border-green-400/40 px-2 py-1 rounded hover:bg-green-400/10">
                  Voir l’espace
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default AlertsPanel;