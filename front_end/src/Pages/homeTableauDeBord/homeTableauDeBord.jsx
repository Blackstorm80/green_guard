import StatCard from "../../components/Dashboard/SanteGlobal";
import ZoneCard from "../../components/Dashboard/Zones";
import InterventionCard from "../../components/Dashboard/InterventionCard";

// function HomeTableauDeBord() {
//   return (
//     <div
//       id="dashboard"
//       className="section-view active space-y-4 md:space-y-6 h-full flex flex-col bg-gray-900 p-3 sm:p-4 md:p-6"
//     >
//       {/* ===== STAT CARDS ===== */}
//       <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6 shrink-0">
//         {/* 1. سلامت کلی */}
//         <StatCard
//           data={{
//             title: "SANTÉ GLOBALE",
//             value: "96.4",
//             unit: "%",
//             subtitle: "+2.1% vs semaine dernière",
//             color: "text-white",
//           }}
//         />
//         <StatCard
//           data={{
//             title: "Santé Globale",
//             value: "96.4",
//             unit: "%",
//             subtitle: "+2.1% vs semaine dernière",
//           }}
//         />

//         <StatCard
//           data={{
//             title: "Température Serveur",
//             value: "42",
//             unit: "°C",
//             subtitle: "+5°C depuis hier",
//           }}
//         />

//         <StatCard
//           data={{
//             title: "Consommation Électrique",
//             value: "1.8",
//             unit: "kW",
//             subtitle: "-0.3kW vs moyenne",
//           }}
//         />

//         <StatCard
//           data={{
//             title: "Espaces en Stress",
//             value: "3",
//             subtitle: "Action immédiate requise",
//             alert: true,
//             alertIcon: "🚨",
//           }}
//         />

//         <StatCard
//           data={{
//             title: "Qualité Air CO²",
//             value: "520",
//             unit: "ppm",
//             subtitle: "+40ppm vs optimal",
//           }}
//         />

//         <StatCard
//           data={{
//             title: "Niveau Batterie",
//             value: "85",
//             unit: "%",
//             subtitle: "+15% en charge",
//           }}
//         />

//         <StatCard
//           data={{
//             title: "Performance Réseau",
//             value: "98",
//             unit: "%",
//             subtitle: "Stable",
//           }}
//         />

//         <StatCard
//           data={{
//             title: "Erreurs Système",
//             value: "3",
//             subtitle: "-2 depuis hier",
//           }}
//         />

//         <StatCard
//           data={{
//             title: "Satisfaction Client",
//             value: "4.8",
//             unit: "/5",
//             subtitle: "+0.3 vs mois dernier",
//           }}
//         />

//         <StatCard
//           data={{
//             title: "Latence Réseau",
//             value: "145",
//             unit: "ms",
//             subtitle: "+25ms depuis hier",
//           }}
//         />

//         {/* 2. دما */}
//         <StatCard
//           data={{
//             title: "TEMPERATURE",
//             value: "42",
//             unit: "°C",
//             subtitle: "+5°C depuis hier",
//             color: "text-white",
//           }}
//         />

//         {/* 3. مصرف برق */}
//         <StatCard
//           data={{
//             title: "CONSOMMATION ÉLECTRIQUE",
//             value: "1.8",
//             unit: "kW",
//             subtitle: "-0.3kW vs moyenne",
//             color: "text-white",
//           }}
//         />

//         {/* 4. فضای استرس */}
//         <StatCard
//           data={{
//             title: "ESPACES EN STRESS",
//             value: "3",
//             subtitle: "Action immédiate requise",
//             alert: true,
//             alertIcon: "🚨",
//           }}
//         />

//         {/* 5. کیفیت هوا */}
//         <StatCard
//           data={{
//             title: "QUALITÉ AIR CO²",
//             value: "520",
//             unit: "ppm",
//             subtitle: "+40ppm vs optimal",
//             color: "text-white",
//           }}
//         />

//         {/* 6. باتری */}
//         <StatCard
//           data={{
//             title: "NIVEAU BATTERIE",
//             value: "85",
//             unit: "%",
//             subtitle: "+15% en charge",
//             color: "text-white",
//           }}
//         />

//         {/* 7. عملکرد شبکه */}
//         <StatCard
//           data={{
//             title: "PERFORMANCE RÉSEAU",
//             value: "98",
//             unit: "%",
//             subtitle: "Stable",
//             color: "text-white",
//           }}
//         />

//         {/* 8. کل فضاها */}
//         <StatCard
//           data={{
//             title: "TOTAL ESPACES",
//             value: "24",
//             subtitle: "Stable",
//             color: "text-white",
//             showIcon: false,
//           }}
//         />
//       </div>

//       {/* ===== MAIN CONTENT ===== */}
//       <div className="flex flex-col lg:flex-row gap-4 md:gap-6 flex-1 min-h-[300px] md:min-h-[400px]">
//         {/* LEFT SIDE - Performance Zones */}
//         <div className="flex-1 flex flex-col gap-3 md:gap-4">
//           <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-2 gap-2">
//             <h3 className="text-white font-semibold flex items-center text-lg md:text-xl">
//               <span className="mr-2">🌍</span> Performance par Secteur
//             </h3>
//             <button className="text-xs text-slate-400 hover:text-white border border-gray-600 px-3 py-1 rounded-lg transition-colors w-full sm:w-auto">
//               Gérer les zones
//             </button>
//           </div>

//           <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
//             {/* CARD 1 - Zone Paris-Nord */}
//             <div className="bg-gray-800 p-4 md:p-5 rounded-xl md:rounded-2xl border border-red-500/40 hover:border-red-500 transition cursor-pointer shadow-lg">
//               <div className="flex flex-col sm:flex-row justify-between items-start mb-3 md:mb-4 gap-2">
//                 <div className="flex-1">
//                   <h4 className="text-white font-bold text-base md:text-lg truncate">
//                     Zone Paris-Nord
//                   </h4>
//                   <p className="text-xs text-slate-400">12 Espaces</p>
//                 </div>
//                 <span className="bg-red-500/20 text-red-400 px-2 py-1 rounded text-xs font-bold self-start sm:self-center">
//                   Stress
//                 </span>
//               </div>

//               <div className="w-full h-2 md:h-3 bg-gray-700 rounded-full overflow-hidden flex mb-2">
//                 <div className="h-full bg-green-500" style={{ width: "75%" }} />
//                 <div
//                   className="h-full bg-yellow-500"
//                   style={{ width: "15%" }}
//                 />
//                 <div
//                   className="h-full bg-red-500 animate-pulse"
//                   style={{ width: "10%" }}
//                 />
//               </div>

//               <div className="flex justify-between text-xs text-slate-400 flex-wrap gap-1">
//                 <span className="text-green-400">9 OK</span>
//                 <span className="text-yellow-400">1 Warning</span>
//                 <span className="text-red-400 font-bold">2 Critiques</span>
//               </div>
//             </div>

//             {/* CARD 2 - Zone Lyon-Est */}
//             <div className="bg-gray-800 p-4 md:p-5 rounded-xl md:rounded-2xl border border-gray-700 hover:border-green-500 transition cursor-pointer shadow-lg">
//               <div className="flex flex-col sm:flex-row justify-between items-start mb-3 md:mb-4 gap-2">
//                 <div className="flex-1">
//                   <h4 className="text-white font-bold text-base md:text-lg truncate">
//                     Zone Lyon-Est
//                   </h4>
//                   <p className="text-xs text-slate-400">12 Espaces</p>
//                 </div>
//                 <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded text-xs font-bold self-start sm:self-center">
//                   Excellent
//                 </span>
//               </div>

//               <div className="w-full h-2 md:h-3 bg-gray-700 rounded-full overflow-hidden flex mb-2">
//                 <div className="h-full bg-green-500" style={{ width: "92%" }} />
//                 <div className="h-full bg-yellow-500" style={{ width: "8%" }} />
//               </div>

//               <div className="flex justify-between text-xs text-slate-400 flex-wrap gap-1">
//                 <span className="text-green-400">11 OK</span>
//                 <span className="text-yellow-400">1 Warning</span>
//                 <span className="text-slate-500">0 Critique</span>
//               </div>
//             </div>
//           </div>
//         </div>

//         {/* RIGHT SIDE - Urgent Interventions */}
//         <div className="w-full lg:w-80 xl:w-96 bg-gray-800 rounded-xl md:rounded-2xl border border-gray-700 flex flex-col shrink-0 shadow-lg mt-4 md:mt-0">
//           <div className="p-3 md:p-4 border-b border-gray-700">
//             <h3 className="text-white font-semibold text-red-500 flex items-center text-base md:text-lg">
//               <span className="mr-2 animate-pulse">⚡</span>
//               <span className="truncate">
//                 Espaces à intervenir en urgence (3)
//               </span>
//             </h3>
//           </div>

//           <div className="p-2 md:p-3 flex-1 overflow-y-auto space-y-2 md:space-y-3">
//             {[
//               {
//                 title: "Toit Bibliothèque Centrale",
//                 label: "Sec",
//                 desc: "Humidité sol critique (22%).",
//                 priority: "high",
//               },
//               {
//                 title: "Mur Mairie Sud",
//                 label: "Mortalité",
//                 desc: "Perte massive de signal.",
//                 priority: "critical",
//               },
//               {
//                 title: "Jardin ZAC Nord",
//                 label: "Chaleur",
//                 desc: "Température seuil tolérance.",
//                 priority: "high",
//               },
//             ].map((item, i) => (
//               <div
//                 key={i}
//                 className={`bg-gray-900 p-2 md:p-3 rounded-lg md:rounded-xl border-l-4 ${
//                   item.priority === "critical"
//                     ? "border-red-500"
//                     : "border-orange-500"
//                 } hover:bg-gray-800 transition cursor-pointer`}
//               >
//                 <div className="flex justify-between items-start gap-2">
//                   <span className="text-xs md:text-sm font-bold text-white truncate flex-1">
//                     {item.title}
//                   </span>
//                   <span className="text-[8px] md:text-[10px] bg-red-500 text-white px-1.5 py-0.5 rounded font-bold flex-shrink-0">
//                     {item.label}
//                   </span>
//                 </div>
//                 <p className="text-[10px] md:text-xs text-slate-400 mt-1 truncate">
//                   {item.desc}
//                 </p>
//               </div>
//             ))}
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default HomeTableauDeBord;


function HomeTableauDeBord() {
  const metricsData = [
    {
      id: 1,
      title: "ESPACES EN STRESS",
      value: "3",
      subtitle: "Action immédiate requise",
      alert: true,
      alertIcon: "🚨",
      priority: "critical",
    },

    {
      id: 2,
      title: "Qualité Air CO²",
      value: "520",
      unit: "ppm",
      subtitle: "+40ppm vs optimal",
      priority: "high",
    },
    {
      id: 3,
      title: "Latence Réseau",
      value: "145",
      unit: "ms",
      subtitle: "+25ms depuis hier",
      priority: "high",
    },
    {
      id: 4,
      title: "Erreurs Système",
      value: "3",
      subtitle: "-2 depuis hier",
      priority: "high",
    },

    {
      id: 5,
      title: "Température Serveur",
      value: "42",
      unit: "°C",
      subtitle: "+5°C depuis hier",
      priority: "medium",
    },
    {
      id: 6,
      title: "Consommation Électrique",
      value: "1.8",
      unit: "kW",
      subtitle: "-0.3kW vs moyenne",
      priority: "medium",
    },

    {
      id: 7,
      title: "SANTÉ GLOBALE",
      value: "96.4",
      unit: "%",
      subtitle: "+2.1% vs semaine dernière",
      priority: "low",
    },
    {
      id: 8,
      title: "Santé Globale",
      value: "96.4",
      unit: "%",
      subtitle: "+2.1% vs semaine dernière",
      priority: "low",
    },
    {
      id: 9,
      title: "Niveau Batterie",
      value: "85",
      unit: "%",
      subtitle: "+15% en charge",
      priority: "low",
    },
    {
      id: 10,
      title: "Performance Réseau",
      value: "98",
      unit: "%",
      subtitle: "Stable",
      priority: "low",
    },
    {
      id: 11,
      title: "TOTAL ESPACES",
      value: "24",
      subtitle: "Stable",
      showIcon: false,
      priority: "low",
    },
    {
      id: 12,
      title: "Satisfaction Client",
      value: "4.8",
      unit: "/5",
      subtitle: "+0.3 vs mois dernier",
      priority: "low",
    },
    {
      id: 13,
      title: "TEMPERATURE",
      value: "42",
      unit: "°C",
      subtitle: "+5°C depuis hier",
      priority: "medium",
    },
    {
      id: 14,
      title: "CONSOMMATION ÉLECTRIQUE",
      value: "1.8",
      unit: "kW",
      subtitle: "-0.3kW vs moyenne",
      priority: "medium",
    },
    {
      id: 15,
      title: "QUALITÉ AIR CO²",
      value: "520",
      unit: "ppm",
      subtitle: "+40ppm vs optimal",
      priority: "high",
    },
    {
      id: 16,
      title: "NIVEAU BATTERIE",
      value: "85",
      unit: "%",
      subtitle: "+15% en charge",
      priority: "low",
    },
    {
      id: 17,
      title: "PERFORMANCE RÉSEAU",
      value: "98",
      unit: "%",
      subtitle: "Stable",
      priority: "low",
    },
  ];

  const sortedMetrics = [...metricsData].sort((a, b) => {
    const priorityOrder = { critical: 1, high: 2, medium: 3, low: 4 };
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });

  const criticalCount = sortedMetrics.filter(
    (m) => m.priority === "critical"
  ).length;
  const highCount = sortedMetrics.filter((m) => m.priority === "high").length;
  const mediumCount = sortedMetrics.filter(
    (m) => m.priority === "medium"
  ).length;
  const lowCount = sortedMetrics.filter((m) => m.priority === "low").length;

  const handleZoneClick = (zoneId) => {
    console.log(`Zone cliquée: ${zoneId}`);
  };

  const handleInterventionClick = (title) => {
    console.log(`Intervention cliquée: ${title}`);
  };

  return (
    <div
      id="dashboard"
      className="section-view active space-y-6 h-full flex flex-col"
    >
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div>
            <h2 className="text-lg font-bold text-white">
              Indicateurs de Performance
            </h2>
            <p className="text-sm text-slate-400">
              {sortedMetrics.length} métriques • Triées par priorité
            </p>
          </div>

          <div className="text-center">
            <div className="inline-flex items-center gap-4 text-sm bg-gray-800/50 px-4 py-2 rounded-lg">
              <span className="text-slate-300">📊 Résumé:</span>

              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-red-500 rounded-full animate-[ping_1.5s_ease-in-out_infinite]"></div>
                <span className="text-red-400 font-semibold">
                  {criticalCount} critique
                </span>
              </div>

              <div className="flex items-center gap-1">
                <div className="w-2.5 h-2.5 bg-red-400 rounded-full"></div>
                <span className="text-red-300">{highCount} élevé</span>
              </div>

              <div className="flex items-center gap-1">
                <div className="w-2.5 h-2.5 bg-yellow-500 rounded-full"></div>
                <span className="text-yellow-400">{mediumCount} moyen</span>
              </div>

              <div className="flex items-center gap-1">
                <div className="w-2.5 h-2.5 bg-green-500 rounded-full"></div>
                <span className="text-green-400">{lowCount} bon</span>
              </div>
            </div>
          </div>
        </div>

        <div className="h-[400px] overflow-y-auto bg-gray-800/30 rounded-xl border border-gray-700 p-4">
          <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
            {sortedMetrics.map((metric) => (
              <div
                key={metric.id}
                className={`relative ${
                  metric.priority === "critical"
                    ? "ring-2 ring-red-500 ring-opacity-50"
                    : metric.priority === "high"
                    ? "ring-1 ring-red-400 ring-opacity-30"
                    : metric.priority === "medium"
                    ? "ring-1 ring-yellow-500 ring-opacity-30"
                    : ""
                } rounded-xl hover:ring-opacity-70 transition-all`}
              >
                <div
                  className={`absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold z-10 ${
                    metric.priority === "critical"
                      ? "bg-red-500 text-white shadow-lg"
                      : metric.priority === "high"
                      ? "bg-red-400 text-white"
                      : metric.priority === "medium"
                      ? "bg-yellow-500 text-black"
                      : "bg-green-500 text-white"
                  }`}
                >
                  {metric.priority === "critical"
                    ? "!"
                    : metric.priority === "high"
                    ? "H"
                    : metric.priority === "medium"
                    ? "M"
                    : "✓"}
                </div>

                <StatCard data={metric} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ===== MAIN CONTENT ===== */}
      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-[400px]">
        {/* LEFT */}
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-white font-semibold flex items-center">
              <span className="mr-2">🌍</span> Performance par Secteur
            </h3>
            <button className="text-xs text-slate-400 hover:text-white border border-gray-600 px-3 py-1 rounded-lg transition-colors">
              Gérer les zones
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ZoneCard
              data={{
                title: "Zone Paris-Nord",
                spacesCount: 12,
                status: "stress",
                okCount: 9,
                warningCount: 1,
                criticalCount: 2,
                subtitle: "3 espaces nécessitent une intervention",
                onClick: () => handleZoneClick("paris-nord"),
              }}
            />

            <ZoneCard
              data={{
                title: "Zone Lyon-Est",
                spacesCount: 12,
                status: "excellent",
                okCount: 11,
                warningCount: 1,
                criticalCount: 0,
                subtitle: "Performance optimale",
                onClick: () => handleZoneClick("lyon-est"),
              }}
            />
          </div>
        </div>

        {/* RIGHT - Urgent Interventions */}
        <div className="w-full lg:w-96 bg-gray-800 rounded-2xl border border-gray-700 flex flex-col shrink-0 shadow-lg">
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-white font-semibold text-red-500 flex items-center">
              <span className="mr-2 animate-pulse">⚡</span>
              Espaces à intervenir en urgence (3)
            </h3>
          </div>

          <div className="p-3 flex-1 overflow-y-auto space-y-3">
            <InterventionCard
              data={{
                title: "Toit Bibliothèque Centrale",
                label: "Sec",
                desc: "Humidité sol critique (22%). Niveau critique atteint.",
                priority: "auto",
                onClick: () => handleInterventionClick("Toit Bibliothèque Centrale"),
              }}
            />

            <InterventionCard
              data={{
                title: "Mur Mairie Sud",
                label: "Mortalité",
                desc: "Perte massive de signal végétal. Mortalité détectée.",
                priority: "auto",
                onClick: () => handleInterventionClick("Mur Mairie Sud"),
              }}
            />

            <InterventionCard
              data={{
                title: "Jardin ZAC Nord",
                label: "Chaleur",
                desc: "Température seuil tolérance dépassé.",
                priority: "auto",
                onClick: () => handleInterventionClick("Jardin ZAC Nord"),
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomeTableauDeBord;
