// function PlantCard({ plant }) {
//   return (
//     <div className="bg-gray-800 rounded-2xl border border-gray-700 p-4 text-left hover:border-green-500 transition cursor-pointer group">
//       <div className="w-full h-32 bg-gray-700 rounded-xl mb-3 flex items-center justify-center text-4xl">
//         {plant.icon}
//       </div>

//       <h3 className="text-sm font-bold text-white group-hover:text-green-400 transition">
//         {plant.name}
//       </h3>

//       <p className="text-xs text-slate-400 mt-1">
//         {plant.type}
//       </p>

//       <div className="mt-3 flex flex-wrap gap-2">
//         <span className="text-[10px] bg-blue-900/40 text-blue-300 px-2 py-1 rounded">
//           Eau: {plant.water}
//         </span>

//         <span className="text-[10px] bg-yellow-900/40 text-yellow-300 px-2 py-1 rounded">
//           {plant.exposure}
//         </span>
//       </div>
//     </div>
//   );
// }

// export default PlantCard;
import { useState } from "react";

function PlantCard({ plant }) {
  // وضعیتی برای چک کردن اینکه آیا عکس با موفقیت لود شده یا خیر
  const [imageError, setImageError] = useState(false);

  return (
    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-4 text-left hover:border-green-500 transition-all duration-300 cursor-pointer group shadow-lg">
      
      {/* Container Image - مدیریت هوشمند ابعاد و خطا */}
      <div className="w-full h-40 bg-gray-900 rounded-xl mb-4 overflow-hidden flex items-center justify-center p-2 border border-gray-700/50 relative">
        
        {!imageError && plant.imageUrl ? (
          <img
            src={plant.imageUrl}
            alt={plant.name}
            // اگر عکس لود نشد، تابعonError اجرا می‌شود
            onError={() => setImageError(true)}
            className="w-full h-full object-contain transition-transform duration-500 group-hover:scale-110"
          />
        ) : (
          /* نمایش ایموجی در صورتی که عکس نباشد یا لود نشود */
          <div className="flex flex-col items-center gap-2">
            <span className="text-5xl drop-shadow-md">{plant.icon || "🌿"}</span>
            <span className="text-[10px] text-gray-500 uppercase font-bold">Image non disp.</span>
          </div>
        )}
      </div>

      {/* Détails */}
      <h3 className="text-sm font-bold text-white group-hover:text-green-400 transition-colors uppercase tracking-wider">
        {plant.name}
      </h3>

      <p className="text-[11px] text-slate-400 mt-1 italic min-h-[32px]">
        {plant.type}
      </p>

      {/* Badges Info */}
      <div className="mt-4 flex flex-wrap gap-2">
        <div className="flex items-center gap-1 text-[10px] bg-blue-900/30 text-blue-300 px-2 py-1 rounded-full border border-blue-800/50">
          <span>💧</span>
          <span>Eau: {plant.water}</span>
        </div>

        <div className="flex items-center gap-1 text-[10px] bg-yellow-900/30 text-yellow-300 px-2 py-1 rounded-full border border-yellow-800/50">
          <span>☀️</span>
          <span>{plant.exposure}</span>
        </div>
      </div>
    </div>
  );
}

export default PlantCard;